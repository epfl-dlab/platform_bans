from datetime import timedelta
import pandas as pd
import numpy as np
import re


def groupact(x):
    if x < 10:
        return "[0-10)"
    if x < 30:
        return "[10-30)"
    if x < 100:
        return "[30-100)"
    else:
        return "[100,)"


def get_matched_dataframes(df_, reddit_venue, fringe_venue, migration_date, grace_period, days_before, days_after):
    def fix_percentages(df_content):
        df_content["fixation_dict_incels"] = df_content["fixation_dict_incels"] / df_content["count_repeated"]
        df_content["fixation_dict_td"] = df_content["fixation_dict_td"] / df_content["count_repeated"]
        df_content["NegativeEmotion"] = df_content["NegativeEmotion"] / df_content["count_repeated"]
        df_content["CoreHostility"] = df_content["CoreHostility"] / df_content["count_repeated"]
        df_content["They:"] = df_content["They:"] / df_content["count_repeated"]
        df_content["We:"] = df_content["We:"] / df_content["count_repeated"]
        df_content.loc[:, ["SEVERE_TOXICITY", "SEVERE_TOXICITY80p", "fixation_dict_incels", "fixation_dict_td",
                           'NegativeEmotion', 'CoreHostility', "They:", "We:"]] *= 100
        df_content = df_content.rename({"We:": "We", "They:": "They"}, axis=1)
        return df_content

    # gets only relevant dates
    df = df_.loc[(((df_.venue == reddit_venue) | (df_.venue == fringe_venue)) &
                  (df_.date_post >= migration_date - timedelta(days=days_before)) &
                  (df_.date_post <= migration_date + timedelta(days=days_after)))]

    # gets author names
    authors_reddit = list(set(df.loc[(df.venue == reddit_venue) &
                                     (df.date_post < migration_date)].author))

    authors_fringe = list(set(df.loc[(df.venue == fringe_venue) &
                                     (df.date_post >= migration_date)].author))

    # performs exact matching
    authors_reddit_d = {re.sub("[^A-Za-z0-9]", "", name).lower(): name for name in authors_reddit}
    authors_reddit_r = {i: k for k, i in authors_reddit_d.items()}
    authors_fringe_d = {re.sub("[^A-Za-z0-9]", "", name).lower(): name for name in authors_fringe}
    authors_fringe_r = {i: k for k, i in authors_fringe_d.items()}
    exact_match = set(authors_reddit_d.keys()).intersection(set(authors_fringe_d.keys()))
    pairs = [(authors_reddit_d[m], authors_fringe_d[m]) for m in exact_match if len(m) > 0]

    # gets count before and after
    df_before = df.loc[((df.venue == reddit_venue) &
                        (df.date_post >= migration_date - timedelta(days=days_before)) &
                        (df.date_post < migration_date))]
    df_before["kind"] = "before"

    df_after = df.loc[((df.venue == fringe_venue) &
                       (df.date_post >= migration_date) &
                       (df.date_post <= migration_date + timedelta(days=days_after)))]
    df_after["kind"] = "after"

    dict_to_agg = {
        "body": len,
        "SEVERE_TOXICITY": np.max,
        "SEVERE_TOXICITY80p": np.mean,
        'fixation_dict_incels': np.nansum,
        'fixation_dict_td': np.nansum,
        'NegativeEmotion': np.nansum,
        'CoreHostility': np.nansum,
        'We:': np.nansum,
        'They:': np.nansum,
        'length': np.nanmedian,
        'count_repeated': np.nansum
    }

    df_before_gb = df_before.groupby("author").agg( dict_to_agg).reset_index()
    df_before_gb["kind"] = "before"
    df_before_gb = fix_percentages(df_before_gb)

    df_after_gb = df_after.groupby("author").agg(dict_to_agg).reset_index()
    df_after_gb["kind"] = "after"
    df_after_gb = fix_percentages(df_after_gb)

    # Does matching
    set_before = set([p[0] for p in pairs])
    df_before_matched = df_before_gb.loc[df_before_gb.author.apply(lambda x: x in set_before)]
    df_before_matched["author"] = df_before_matched["author"].apply(lambda x: authors_reddit_r[x])
    df_before_matched = df_before_matched.set_index("author")

    set_after = set([p[1] for p in pairs])
    df_after_matched = df_after_gb.loc[df_after_gb.author.apply(lambda x: x in set_after)]
    df_after_matched["author"] = df_after_matched["author"].apply(lambda x: authors_fringe_r[x])
    df_after_matched = df_after_matched.set_index("author")

    df_before_after = df_before_matched.merge(df_after_matched, left_index=True, right_index=True)
    df_before_after.rename({"body_x": "before", "body_y": "after"}, axis=1, inplace=True)

    # get quartiles
    quintiles = np.nanquantile(df_before_after.before.values, np.arange(0, 1, 0.25))
    print("quartiles before", quintiles)
    df_before_after["ptile"] = df_before_after.before.apply(lambda x: np.argmin(x >= quintiles)
                                                                      + 4 * (x >= max(quintiles)))
    quintiles_after = np.nanquantile(df_before_after.after.values, np.arange(0, 1, 0.25))
    df_before_after["ptile_after"] = df_before_after.after.apply(lambda x: np.argmin(x >= quintiles_after)
                                                                           + 4 * (x >= max(quintiles_after)))

    df_before_after["group_after"] = df_before_after.after.apply(groupact)
    quintiles = np.nanquantile(df_after_gb.body.values, np.arange(0, 1, 0.25), interpolation="nearest")
    print("quartiles after", quintiles)

    df_before_gb["ptile"] = df_before_gb.body.apply(lambda x: np.argmin(x >= quintiles)
                                                              + 4 * (x >= max(quintiles)))

    df_after_gb["ptile"] = df_after_gb.body.apply(lambda x: np.argmin(x >= quintiles)
                                                            + 4 * (x >= max(quintiles)))

    # concats
    df_gb = pd.concat([df_before_gb, df_after_gb])
    df_users_matched = pd.concat(
        [df_before.loc[df_before.author.apply(lambda x: x in set_before)],
         df_after.loc[df_after.author.apply(lambda x: x in set_after)]])

    return pairs, df_users_matched, df_gb, df_before_after
