# Do Platform Migrations Compromise Content Moderation? Evidence from r/The_Donald and r/Incels

This repo contains the data and the analysis done in the paper "Do Platform Migrations Compromise Content Moderation? 
Evidence from r/The_Donald and r/Incels".
Please cite as:

~~~bibtex
@inproceedings{ribeiro2021migrations,
    title={Do Platform Migrations Compromise Content Moderation? 
        Evidence from r/The_Donald and r/Incels},
    author={Ribeiro, Manoel Horta and
        Jhaver, Shagun and 
        Zannettou, Savvas and 
        Blackburn, Jeremy and 
        De Cristofaro, Emiliano and 
        Stringhini, Gianluca and 
        West, Robert},
    booktitle={Proceedings of the ACM on Human-Computer Interaction (CSCW)},
    year={2021}
}
~~~

Other useful links:

- arXiV version;
- reproducibility data;
- presentation;

## Brief description of data

`activity_agg.csv`:  aggregated activity signals.
- `venue`: `/r/Incels` or `/r/The_Donald`
- `date_post`: date;
- `id`: number of posts;
- `author`: number of authors;
- `length`: median post length;
- `first`: number of newcomers;
- `idpauthor`: number of posts per author;
- `intervention_flag`: 0 if before the migration, 1 otherwise;
- `date_idx` date relative to the migration day;

`content(_matched)?_agg(_fixation_dict)?`: aggregated content signals. If file name contains `_matched`, 
it has data only for matched users, if file name contains `fixation_dict`, it has data only for posts containing one of
 the words in the fixation dictionary.
- `venue`: `/r/Incels` or `/r/The_Donald`
- `date_post`: date;
- `SEVERE_TOXICITY80p`: percentage of posts with >0.8 toxicity.
- `fixation_dict_incels` ,` fixation_dict_td`, `NegativeEmotion`, `CoreHostility` , `We`, `They`: number of occurrences 
in each category divided by number of words.
- `length`: median post length;
- `intervention_flag`: 0 if before the migration, 1 otherwise;
- `date_idx` date relative to the migration day;

`users_td.csv` and `users_incels.csv`: user-level aggregated signals (one file per community; one user per line).
- `num_posts`: number of posts;
- `SEVERE_TOXICITY80p`: percentage of posts with >0.8 toxicity.
- `fixation_dict_incels`, `fixation_dict_td`, `NegativeEmotion`, `CoreHostility`, `We`, `They`: number of occurrences in
 each category divided by number of words.
- `length`: median post length;
- `ptile`: activity quartile of the user in the pre-migration period;
- `kind`: `before` if before the migration, `after` if after the migration;

`users_matched_incels(_f)?.csv` and `users_matched_incels(_f)?.csv`: data comparing matched users (before vs. after 
migration, one user per line, one file per community). If file name contains `_f`, it has data only for posts containing
 one of the words in the fixation dictionary. Fields are the same as in `users_td.csv` and `users_incels.csv` appended
 with `_x` if considering the period before the migration and with `_y` if considering the period after.

## Brief description of code

- `01_data_wrangling.ipynb` gets data ready, you only have access to the output of this notebook.
- `02_community_level.ipynb` reproduces community-level figures and tables (Fig 3, 6, 8; Table 3).
- `03_user_level.ipynb` reproduces user-level figures (Fig 4, 5, 7).
