from helpers.vars import interventions
import statsmodels.formula.api as smf
from datetime import timedelta
import pandas as pd
import numpy as np
import math


def get_first(x):
    x_ = abs(x)

    decimal_part = abs(x_ - float(int(x_)))
    max0s = 3
    if x_ > 1:
        max0s = 1
    if x_ > 10:
        max0s = 1
    if x_ > 1000:
        max0s = 0

    if x == 0.0:
        return "0.001"

    first_non0 = math.ceil(abs(np.log10(decimal_part)))

    strv = str(round(x, min(first_non0, max0s)))
    if strv[-2:] == ".0":
        strv = strv[:-2]

    if strv == "-0":
        strv = "-0.001"
    if strv == "0":
        strv = "0.001"
    return strv


def get_content_helper(df, days_before=120, days_after=119):
    df["fixation_dict_incels_norm"] = df["fixation_dict_incels"] / df["count_repeated"]
    df["fixation_dict_td_norm"] = df["fixation_dict_td"] / df["count_repeated"]
    df["NegativeEmotion_norm"] = df["NegativeEmotion"] / df["count_repeated"]
    df["CoreHostility_norm"] = df["CoreHostility"] / df["count_repeated"]
    df["They_norm"] = df["They:"] / df["count_repeated"]
    df["We_norm"] = df["We:"] / df["count_repeated"]

    # Gets mean values per day per venue
    df_content = df.loc[(~df.body.isna()) & (df["type"] == "comment")] \
        .groupby(["venue", pd.Grouper(key='date_post', freq='d')]) \
        .agg({'SEVERE_TOXICITY': np.nanmean,
              'SEVERE_TOXICITY80p': np.nanmean,
              'fixation_dict_incels': np.nansum,
              'fixation_dict_td': np.nansum,
              'NegativeEmotion': np.nansum,
              'CoreHostility': np.nansum,
              'We:': np.nansum,
              'They:': np.nansum,
              'fixation_dict_incels_norm': np.nanmean,
              'fixation_dict_td_norm': np.nanmean,
              'NegativeEmotion_norm': np.nanmean,
              'CoreHostility_norm': np.nanmean,
              'We_norm': np.nanmean,
              'They_norm': np.nanmean,
              'length': np.nanmedian,
              'count_repeated': np.nansum
              }).reset_index()

    # Restricts data to 60 days before and after intervention
    df_content = df_content.loc[
        get_slice_date_venue(df_content, "/r/The_Donald",
                             interventions["/r/The_Donald"]["Measure"], days_before, days_after) |
        get_slice_date_venue(df_content, "/r/Incels",
                             interventions["/r/Incels"]["Measure"], days_before, days_after)
        ]

    df_content["fixation_dict_incels"] = df_content["fixation_dict_incels"] / df_content["count_repeated"]
    df_content["fixation_dict_td"] = df_content["fixation_dict_td"] / df_content["count_repeated"]
    df_content["NegativeEmotion"] = df_content["NegativeEmotion"] / df_content["count_repeated"]
    df_content["CoreHostility"] = df_content["CoreHostility"] / df_content["count_repeated"]
    df_content["They:"] = df_content["They:"] / df_content["count_repeated"]
    df_content["We:"] = df_content["We:"] / df_content["count_repeated"]

    # sets intervention stuff
    df_content["intervention_flag"] = 0
    set_intervention_stuff(df_content, "/r/Incels", interventions["/r/Incels"]["Measure"])
    set_intervention_stuff(df_content, "/r/The_Donald", interventions["/r/The_Donald"]["Measure"])
    df_content.date_idx = df_content.date_idx.apply(lambda x: x.days)

    df_content.loc[:, ["SEVERE_TOXICITY", "SEVERE_TOXICITY80p", "fixation_dict_incels", "fixation_dict_td",
                       'NegativeEmotion', 'CoreHostility', "They:", "We:"]] *= 100

    df_content = df_content.rename({"We:": "We", "They:": "They"}, axis=1)

    return df_content


def exclude_dates_helper(date_post, exclude_dates):
    to_exc = None
    for start, end in exclude_dates:
        if to_exc is None:
            to_exc = (date_post >= start) & \
                     (date_post <= end)
        else:
            to_exc = (to_exc) | (date_post >= start) & (date_post <= end)
    return to_exc


def get_coms(venue, exclude_dates, community):
    if venue in exclude_dates:
        to_exc = exclude_dates_helper(community.date_post, exclude_dates[venue])
        community_exc = community.loc[to_exc]
        community = community.loc[~to_exc]
        coms = [community, community_exc]
    else:
        coms = [community]
    return coms


def get_slice_date_venue(df, venue, intervention_date, days_before, days_after):
    return (df.venue == venue) & \
           (df.date_post > intervention_date - timedelta(days=days_before)) & \
           (df.date_post < intervention_date + timedelta(days=days_after))


def set_intervention_stuff(df, venue, intervention_date):
    df.loc[(df.venue == venue) &
           (df.date_post >= intervention_date),
           "intervention_flag"] = 1
    df.loc[(df.venue == venue), "date_idx"] = \
        df.loc[(df.venue == venue), "date_post"] - intervention_date


def regression_helper(df, venues, vals, exclude_dates, grace_period, quintiles=1, confounder=None,
                      grace_period_days=None, round_val=5, out_dir="./data/reproducibility_data/reg_logs/", name_v=""):
    def pvalstars(x):
        if x <= 0.001:
            return "***"
        if x <= 0.01:
            return "**"
        if x <= 0.05:
            return "*"
        return ""

    df_table_ = []

    if quintiles == 1:
        df["quintile"] = 1

    for quint in range(1, quintiles + 1, 1):
        for idx, venue in enumerate(venues):
            # print(venue)
            community = df.loc[(df.venue == venue) & (df.quintile == quint)]

            # handles invalid dates & grace period
            if grace_period is not None and exclude_dates is not None:
                if venue in exclude_dates:
                    to_exc = exclude_dates_helper(community.date_post, exclude_dates[venue])
                    community_exc = community.loc[to_exc]
                    community = community.loc[~to_exc]
                    coms = [community, community_exc]
                else:
                    coms = [community]

                start, end = grace_period[venue]
                to_exc = (community.date_post >= start) & \
                         (community.date_post <= end)
                community_reg = coms[0].loc[~to_exc]
            elif grace_period_days is not None:
                to_exc = (community.date_post >= -grace_period_days) & \
                         (community.date_post <= grace_period_days)
                community_reg = community.loc[~to_exc]

            for idy, val in enumerate(vals):
                reg_log = out_dir + name_v + "_" + val + "_" + venue.replace("/r/", "") + ".txt"
                add_conf = " + {}".format(confounder) if confounder is not None else ""
                mod = smf.ols("{} ~ date_idx * intervention_flag".format(val) + add_conf,
                              data=community_reg[~community_reg[val].isna()])
                res = mod.fit(cov_type='hc0')

                with open(reg_log, "w") as f:
                    f.write(res.summary().as_csv())

                params = {"val": val, "venue": venue, "quint": quint}
                params["rsquared"] = res.rsquared
                params.update(dict(res.params))
                # print(venue, val, params, "\n")

                add_conf_val = params[confounder] * np.mean(community_reg[confounder]) if confounder is not None else 0
                community_reg[val + "reg" + venue + str(quint)] = params['Intercept'] + \
                                                                  params['date_idx'] * community_reg['date_idx'] + \
                                                                  params['intervention_flag'] * community_reg[
                                                                      'intervention_flag'] + \
                                                                  params['date_idx:intervention_flag'] * community_reg[
                                                                      'date_idx'] * \
                                                                  community_reg['intervention_flag'] + add_conf_val
                community_reg["quintile"] = quint
                if val + "reg" + venue + str(quint) in df.columns:
                    df.drop(val + "reg" + venue + str(quint), axis=1, inplace=True)
                df = df.merge(community_reg.loc[:, ["venue", "date_idx", "quintile",
                                                    val + "reg" + venue + str(quint)]],
                              left_on=["venue", "date_idx", "quintile"],
                              right_on=["venue", "date_idx", "quintile"],
                              how="left")

                lower_params = {k + "_low": v for k, v in dict(res.conf_int()[0]).items()}
                upper_params = {k + "_high": v for k, v in dict(res.conf_int()[1]).items()}
                p_vals = {k + "_pval": v for k, v in dict(res.pvalues).items()}

                params.update(lower_params)
                params.update(upper_params)
                params.update(p_vals)

                df_table_.append(params)

    df_table = pd.DataFrame(df_table_)

    to_fix = [x for x in df_table.columns[4:] if "_high" not in x and "_low" not in x and "_pval" not in x]

    def format_data(df_, fix, round_vals):

        df = dict(df_)
        if not round_vals:
            smaller_001 = abs(df[fix]) < 0.01
            if smaller_001:
                df[fix] *= 10 ** 3
                df[fix + "_low"] *= 10 ** 3
                df[fix + "_high"] *= 10 ** 3
            prec = r'[10^{-3}] ' if smaller_001 else ""
        else:
            prec = ""

        first = get_first(df[fix])
        low = get_first(df[fix + "_low"])
        high = get_first(df[fix + "_high"])
        pvals = pvalstars(df[fix + "_pval"])

        return "$" + prec + str(first) + "^{" + pvals + "} (" + str(low) + ", " + str(high) + ")$"

    for fix in to_fix:
        df_table[fix + "_table"] = df_table.apply(lambda x: format_data(x, fix, round_vals=False), axis=1)
        df_table[fix] = df_table.apply(lambda x: format_data(x, fix, round_vals=True), axis=1)

        df_table.drop([fix + "_low", fix + "_high", fix + "_pval"], axis=1, inplace=True)
    df_table["rsquared"] = "$" + df_table["rsquared"].apply(lambda x: str(round(x, 2))) + "$"

    if quintiles == 1:
        df.drop("quintile", axis=1, inplace=True)
        df_table.drop("quint", axis=1, inplace=True)

    return df_table, df
