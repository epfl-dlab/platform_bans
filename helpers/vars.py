import pandas as pd

interventions = {
    "/r/The_Donald": {
        "Measure": pd.to_datetime("2020-02-26"),

    },
    "/r/Incels": {
        "Measure": pd.to_datetime("2017-11-07"),
    }
}

interventions_num = {
    "/r/The_Donald": {
        "Measure": 0,

    },
    "/r/Incels": {
        "Measure": 0,
    }
}

grace_period = {
    "/r/The_Donald": (pd.to_datetime("2020-02-11"),
                      pd.to_datetime("2020-03-12")),
    "/r/Incels": (pd.to_datetime("2017-10-23"),
                  pd.to_datetime("2017-11-22"))
}

grace_period_num = {
    "/r/The_Donald": (-7, 7),
    "/r/Incels": (-7, 7)
}

exclude_dates = {
    "/r/Incels": [(pd.to_datetime("2017-09-20"),
                   pd.to_datetime("2017-09-28")),
                  (pd.to_datetime("2017-07-23"),
                   pd.to_datetime("2017-08-08"))],
    "/r/The_Donald": [(pd.to_datetime("2019-11-21"),
                       pd.to_datetime("2019-11-22")),
                      (pd.to_datetime("'2020-02-05"),
                       pd.to_datetime("'2020-02-05"))]
}

interventions_helper = {
    "Measure": ""
}

int_ls = {
    "Measure": "-",
}

int_c = {
    "Measure": "black",
}
