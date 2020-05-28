from os import path
import json

from configargparse import ArgParser
from scipy import stats as sps
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _99_shared_functions import power_spline, logistic, rel_effect_wrapper, \
    write_pickle
from utils import DirectoryType
import warnings

# plot of chains
def plt_predictive(
    df,
    first_day,
    census_ts,
    figdir,
    as_of_days_ago,
    howfar=200,
    y_max=None,
    prefix="",
    hosp_capacity=None,
    vent_capacity=None,
):
    # predictive plot
    file_howfar = howfar
    arrs = np.stack([df.arr.iloc[i] for i in range(df.shape[0])])
    arrq = np.quantile(arrs, axis=0, q=[0.025, 0.25, 0.5, 0.75, 0.975])
    howfar = len(census_ts.hosp.dropna()) + howfar
    howfar = np.min([howfar, arrs.shape[1]])

    dates = pd.date_range(f"{first_day}", periods=howfar, freq="d")
    fig, ax = plt.subplots(figsize=(16, 10), ncols=2, nrows=2, sharex=True)
    # hosp
    axx = ax[0, 0]
    if y_max:
        axx.set_ylim((0, y_max))
    axx.plot_date(dates, arrq[2, :howfar, 3], "-", label="posterior median")
    axx.set_ylabel(f"COVID-19 Hospital census", fontsize=12, fontweight="bold")
    axx.fill_between(
        x=dates,
        y1=arrq[0, :howfar, 3],
        y2=arrq[4, :howfar, 3],
        label="95% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.fill_between(
        x=dates,
        y1=arrq[1, :howfar, 3],
        y2=arrq[3, :howfar, 3],
        label="50% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.plot_date(
        dates[: census_ts.hosp.loc[census_ts.date >= first_day].shape[0]],
        census_ts.hosp.loc[census_ts.date >= first_day],
        "-",
        color="red",
        label="observed",
    )
    if hosp_capacity:
        axx.axhline(y=hosp_capacity, color="k", ls="--", label="hospital capacity")
    axx.axvline(
        x=dates.values[census_ts.hosp.loc[census_ts.date >= first_day].shape[0] - as_of_days_ago],
        color="grey",
        ls="--",
        label="Last Datapoint Used",
    )

    axx.legend()
    axx.grid(True)

    axx = ax[0, 1]
    if y_max:
        axx.set_ylim((0, y_max))
    axx.plot_date(dates, arrq[2, :howfar, 5], "-", label="posterior median")
    axx.set_ylabel(f"COVID-19 Vent census", fontsize=12, fontweight="bold")
    axx.fill_between(
        x=dates,
        y1=arrq[0, :howfar, 5],
        y2=arrq[4, :howfar, 5],
        label="95% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.fill_between(
        x=dates,
        y1=arrq[1, :howfar, 5],
        y2=arrq[3, :howfar, 5],
        label="50% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.plot_date(
        dates[: census_ts.vent.loc[census_ts.date >= first_day].shape[0]],
        census_ts.vent.loc[census_ts.date >= first_day],
        "-",
        color="red",
        label="observed",
    )
    if vent_capacity:
        axx.axhline(y=vent_capacity, color="k", ls="--", label="vent capacity")
    axx.axvline(
        x=dates.values[census_ts.hosp.loc[census_ts.date >= first_day].shape[0] - as_of_days_ago],
        color="grey",
        ls="--",
        label="Last Datapoint Used",
    )
    axx.legend()
    axx.grid(True)

    # Admits
    axx = ax[1, 0]
    axx.plot_date(dates, arrq[2, :howfar, 0], "-", label="posterior median")
    axx.set_ylabel(f"COVID-19 Hospital Admits", fontsize=12, fontweight="bold")
    axx.fill_between(
        x=dates,
        y1=arrq[0, :howfar, 0],
        y2=arrq[4, :howfar, 0],
        label="95% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.fill_between(
        x=dates,
        y1=arrq[1, :howfar, 0],
        y2=arrq[3, :howfar, 0],
        label="50% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.legend()
    axx.grid(True)

    axx = ax[1, 1]
    axx.plot_date(dates, arrq[2, :howfar, 2], "-", label="posterior median")
    axx.set_ylabel(f"COVID-19 Vent Admits", fontsize=12, fontweight="bold")
    axx.fill_between(
        x=dates,
        y1=arrq[0, :howfar, 2],
        y2=arrq[4, :howfar, 2],
        label="95% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.fill_between(
        x=dates,
        y1=arrq[1, :howfar, 2],
        y2=arrq[3, :howfar, 2],
        label="50% Credible Region",
        alpha=0.1,
        lw=2,
        edgecolor="k",
    )
    axx.legend()
    axx.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path.join(f"{figdir}", f"{prefix}forecast_{file_howfar}_day.pdf"))


def plt_pairplot_posteriors(df, figdir, n=1000, prefix=""):
    import seaborn as sns

    # Create an instance of the PairGrid class.
    grid = sns.PairGrid(data=df.sample(n))

    # Map a scatter plot to the upper triangle
    grid = grid.map_upper(plt.scatter, alpha=0.1)

    # Map a histogram to the diagonal
    grid = grid.map_diag(plt.hist, bins=20)

    # Map a density plot to the lower triangle
    grid = grid.map_lower(sns.kdeplot, cmap="Reds")
    grid.savefig(path.join(f"{figdir}", f"{prefix}posterior_pairplot.pdf"))


def mk_projection_tables(df, first_day, outdir):
    # predictive plot
    arrs = np.stack([df.arr.iloc[i] for i in range(df.shape[0])])
    arrq = np.quantile(arrs, axis=0, q=[0.05, 0.25, 0.5, 0.75, 0.95])
    column_postfix = ["5%", "25%", "Median", "75%", "%95"]

    summary_df_hsp = pd.DataFrame(
        data=arrq[:, :, 3].T,
        columns=[f"Hospitalized Census {pf}" for pf in column_postfix],
    )
    summary_df_icu = pd.DataFrame(
        data=arrq[:, :, 4].T,
        columns=[f"ICU Census {pf}" for pf in column_postfix],
    )
    summary_df_vent = pd.DataFrame(
        data=arrq[:, :, 5].T, columns=[f"Vent Census {pf}" for pf in column_postfix]
    )

    summary_df_hsp_admits = pd.DataFrame(
        data=arrq[:, :, 0].T.astype(int),
        columns=[f"Hospitalized Admits {pf}" for pf in column_postfix],
    )
    summary_df_icu_admits = pd.DataFrame(
        data=arrq[:, :, 1].T.astype(int),
        columns=[f"ICU Admits {pf}" for pf in column_postfix],
    )
    summary_df_vent_admits = pd.DataFrame(
        data=arrq[:, :, 2].T.astype(int),
        columns=[f"Vent Admits {pf}" for pf in column_postfix],
    )

    date_df = pd.DataFrame(
        data=pd.date_range(f"{first_day}", periods=summary_df_hsp.shape[0], freq="d"),
        columns=["date"],
    )

    summary_df = pd.concat(
        [
            date_df,
            summary_df_hsp,
            summary_df_icu,
            summary_df_vent,
            summary_df_hsp_admits,
            summary_df_icu_admits,
            summary_df_vent_admits,
        ],
        1,
    )
    summary_df.to_csv(path.join(f"{outdir}", "forecast.csv"), index=False)


def read_inputs(paramdir):
    with open(path.join(paramdir, "args.json"), "r") as f:
        args = json.load(f)
    census_ts = pd.read_csv(path.join(paramdir, "census_ts.csv"))
    params = pd.read_csv(path.join(paramdir, "params.csv"))
    return census_ts, params, args


def SD_plot(census_ts, params, df, figdir, prefix = ""):
    qlist = []
    if 'beta_spline_coef_0' in df.columns:
        nobs = census_ts.shape[0]
        beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
        beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
        knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
        beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
        b0 = np.array(df.b0)

        for day in range(nobs):
            X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
            XB = X@beta_spline_coefs.T
            sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB)
            qlist.append(np.quantile(sd, [0.05,.25, 0.5, .75, 0.95]))
            # plt.hist(sd)
    else:
        for day in range(census_ts.shape[0]):
            ldist = logistic(
                df.logistic_L, df.logistic_k, df.logistic_x0 - df.offset.astype(int), day
            )
            qlist.append(np.quantile(ldist, [0.05,.25, 0.5, .75, 0.95]))
            
    # logistic SD plot
    qmat = np.vstack(qlist)
    fig = plt.figure()

    plt.plot(list(range(census_ts.shape[0])), 1 - qmat[:, 2])
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=1 - qmat[:, 0],
        y2=1 - qmat[:, 4],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=1 - qmat[:, 1],
        y2=1 - qmat[:, 3],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.ylabel(f"Effect of NPI on transmission")
    plt.xlabel(f"Days since {census_ts[census_ts.columns[0]].values[0]}")
    plt.ylim(0, 1)
    fig.savefig(path.join(f"{figdir}", f"{prefix}effective_soc_dist.pdf"))


def SEIR_plot(df, first_day, howfar, figdir, prefix, census_ts, as_of_days_ago):
    dates = pd.date_range(f"{first_day}", periods=howfar, freq="d")
    fig = plt.figure()
    for letter in ['s', 'e', 'i', 'r']   : 
        list_of_letter_values = [df[letter].iloc[j][df.offset.iloc[j]:] for j in range(len(df[letter]))]
        L = np.stack(list_of_letter_values)
        Lqs = np.quantile(L[:,:howfar], [.025, .05, .25, .5, .75, .95, .975], axis = 0)    /1000 
        plt.plot_date(dates, Lqs[3, :], "-", label = letter)
        plt.fill_between(x = dates,
                         y1 = Lqs[1, :],
                         y2 = Lqs[5, :],
                         alpha = .3)
    plt.axvline(dates.values[census_ts.hosp.shape[0]-as_of_days_ago],         
        color="grey",
        ls="--",
        label="Last Datapoint Used")
    plt.legend()
    plt.grid(True)
    plt.ylabel('Individuals (thousands)')
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path.join(f"{figdir}", f"{prefix}_SEIR_{howfar}_day.pdf"))





def Rt_plot(df, first_day, howfar, figdir, prefix, params, census_ts):
    dates = pd.date_range(f"{first_day}", periods=howfar, freq="d")
    qlist = []
    qlist_beta, qlist_mob = [], []
    if 'beta_spline_coef_0' in df.columns:
        nobs = census_ts.shape[0]
        beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
        beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
        knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
        beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
        b0 = np.array(df.b0)
        for day in range(nobs):
            X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
            XB = X@beta_spline_coefs.T
            mob_effect = df['mob_effect'].apply(lambda x: x[df.offset.iloc[0]+day])
            sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + mob_effect)
            S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
            beta_t = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days
            qlist.append(np.quantile(beta_t, [0.05,.25, 0.5, .75, 0.95]))
            qlist_beta.append(np.quantile(b0 + XB, [0.05,.25, 0.5, .75, 0.95]))
            qlist_mob.append(np.quantile(mob_effect, [0.05,.25, 0.5, .75, 0.95]))
    else:        
        for day in range(census_ts.shape[0]):
            sd = logistic(
                df.logistic_L, df.logistic_k, df.logistic_x0 - df.offset.astype(int), day
            )
            S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
            beta_t = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days
            qlist.append(np.quantile(beta_t, [0.05,.25, 0.5, .75, 0.95]))            
    qmat = np.vstack(qlist)
    #Rt plot
    fig = plt.figure()
    plt.plot(list(range(census_ts.shape[0])), qmat[:, 2])
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat[:, 0],
        y2=qmat[:, 4],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat[:, 1],
        y2=qmat[:, 3],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.ylabel(f"Reproduction number (R) over time, including NPI")
    plt.xlabel(f"Days since {census_ts[census_ts.columns[0]].values[0]}")
    plt.axhline(y=1,      
        color="grey",
        ls="--")
    fig.savefig(path.join(f"{figdir}", f"{prefix}_Rt.pdf"))
    # contribution of beta
    fig = plt.figure()
    qmat_beta = np.vstack(qlist_beta)*-1
    plt.plot(list(range(census_ts.shape[0])), qmat_beta[:, 2])
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat_beta[:, 0],
        y2=qmat_beta[:, 4],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat_beta[:, 1],
        y2=qmat_beta[:, 3],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.ylabel(f"Contribution to Rt")
    plt.xlabel(f"Days since {census_ts[census_ts.columns[0]].values[0]}")
    plt.title('Contribition of non-mobility interventions to Rt')
    fig.savefig(path.join(f"{figdir}", f"{prefix}_Rt_beta.pdf"))

    # contribution of mobility
    fig = plt.figure()
    qmat_mob = np.vstack(qlist_mob)*-1
    plt.plot(list(range(census_ts.shape[0])), qmat_mob[:, 2])
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat_mob[:, 0],
        y2=qmat_mob[:, 4],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.fill_between(
        x=list(range(census_ts.shape[0])),
        y1=qmat_mob[:, 1],
        y2=qmat_mob[:, 3],
        alpha=0.3,
        lw=2,
        edgecolor="k",
    )
    plt.ylabel(f"Contribution to Rt")
    plt.xlabel(f"Days since {census_ts[census_ts.columns[0]].values[0]}")
    plt.title('Contribition of mobility interventions to Rt')
    fig.savefig(path.join(f"{figdir}", f"{prefix}_Rt_mob.pdf"))






# x = np.stack(df.rel_effect_workplaces)
# xq = np.quantile(x, [.05, .25, .5, .75 ,.95], axis = 0)
# for i in range(5):
#     plt.plot(xq[i,:])

# plt.hist(df.mob_residential*-1)


# termlist = ['retail_and_recreation', 'grocery_and_pharmacy', \
#                               'parks', 'transit_stations', 'workplaces', \
#                               'residential']
# fig, ax = plt.subplots(nrows = 6, figsize = (5,20), sharex = True)
# for i, term in enumerate(termlist):
#     ax[i].hist(df[f"mob_{term}"])
#     ax[i].set_xlabel(term)
#     ax[i].axvline(0)
# fig.savefig("/Users/crandrew/Desktop/mobility_firstpass.pdf")





# coef, relative effect in logit space, comparison of what would happen over the next 30 days if 



# effect of mobility types
def dRdmob(df, census_ts, term, outdir, figdir, prefix):
    # relative effect in logit space
    relef = np.quantile(np.stack(df[f"rel_effect_{term}"]), [.025, .25, .5, .75, .975], axis = 0)
    # retro
    startpos_retr = census_ts.loc[~census_ts.hosp.isna()].index.min()
    retr = rel_effect_wrapper(df, term, startpos_retr)
    startpos_pros = census_ts.loc[~census_ts.hosp.isna()].index.max()
    #pros
    pros = rel_effect_wrapper(df, term, startpos_pros)
    savedict = dict(relef = relef,
                    startpos_retr = startpos_retr,
                    retr = retr,
                    startpos_pros = startpos_pros,
                    pros = pros)
    write_pickle(savedict, path.join(f"{outdir}", f"_relef_plotdat_{term}.pkl"))
    #plot
    fig, ax = plt.subplots(ncols = 3, figsize = (15, 5))
    dd = pd.date_range(start = census_ts.date.iloc[0], periods = len(census_ts))
    ax[0].plot_date(dd, 
                  relef[2, :len(census_ts)],"-")
    ax[0].fill_between(x = dd,
                     y1 = relef[0, :len(census_ts)],
                     y2 = relef[4, :len(census_ts)],
                     alpha = .3,
                     label = "95% credible region")
    ax[0].fill_between(x = dd,
                     y1 = relef[1, :len(census_ts)],
                     y2 = relef[3, :len(census_ts)],
                     alpha = .3,
                     label = "50% credible region")
    ax[0].axhline(0, color="k", ls="--", linewidth = .5)
    ax[0].legend()
    ax[0].grid(True)
    ax[0].title.set_text(f'Retrospective: effect of distancing in  {term}')
    ax[0].set_ylabel('Diff hospitalized COVID patients')
    # counterfactual since beginning of outbreak
    ax[1].plot_date(dd[startpos_retr:len(census_ts)], 
                  retr[2, startpos_retr:len(census_ts)],"-")
    ax[1].fill_between(x = dd[startpos_retr:len(census_ts)],
                     y1 = retr[0, startpos_retr:len(census_ts)],
                     y2 = retr[4, startpos_retr:len(census_ts)],
                     alpha = .3,
                     label = "95% credible region")
    ax[1].fill_between(x = dd[startpos_retr:len(census_ts)],
                     y1 = retr[1, startpos_retr:len(census_ts)],
                     y2 = retr[3, startpos_retr:len(census_ts)],
                     alpha = .3, 
                     label = '50% credible region')
    ax[1].axhline(0, color="k", ls="--", linewidth = .5)
    ax[1].legend()
    ax[1].grid(True)
    ax[1].title.set_text(f'Retrospective: effect of distancing in  {term}')
    ax[1].set_ylabel('Diff hospitalized COVID patients')
    # counterfactual projection
    dd = pd.date_range(start = census_ts.date.max(), periods = 60)
    ax[2].plot_date(dd, 
                  pros[2, startpos_pros:(startpos_pros+60)],"-")
    plt.fill_between(x = dd,
                      y1 = pros[0, startpos_pros:(startpos_pros+60)],
                      y2 = pros[4, startpos_pros:(startpos_pros+60)],
                      alpha = .3,
                      label = "95% credible region")
    ax[2].fill_between(x = dd,
                     y1 = pros[1, startpos_pros:(startpos_pros+60)],
                     y2 = pros[3, startpos_pros:(startpos_pros+60)],
                     alpha = .3, 
                     label = '50% credible region')
    ax[2].axhline(0, color="k", ls="--", linewidth = .5)
    ax[2].legend()
    ax[2].grid(True)
    ax[2].title.set_text(f'Prospective: effect of relaxing {term}')
    ax[2].set_ylabel('Diff hospitalized COVID patients')
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path.join(f"{figdir}", f"{prefix}_relative_effect_{term}.pdf"))

# @@@
# TOMORROW:  get this working with a trimmed -down dataframe.  establish that it works when there are very few iterations.  
# LOOK INTO THE ISSUE WITH NON-ZERO DIFFERENCES AT THE OUTSET    


    
    
# mobarr = np.stack([np.stack(df[term]) for term in termlist])
# coefs = np.stack([df[f"mob_{term}"] for term in termlist])
# rep_coefs = np.stack([coefs for i in range(mobarr.shape[2])], axis = 2)
# baseline = np.sum(mobarr * rep_coefs, axis = 0)
# qlist = []
# for day in range(startpos, startpos+howfar):
#     X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
#     XB = X@beta_spline_coefs.T
#     sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + baseline[:,day])
#     S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#     Rt = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days        
#     qlist.append(Rt)
# b_qmat = np.quantile(np.stack(qlist), [.025, .25, .5, .75, .975], axis = 1)


# for i, term in enumerate(termlist):
#     arr_i = mobarr.copy()
#     arr_i[i, :, startpos:(startpos+howfar)] = 0
#     counterfactual = np.sum(arr_i * rep_coefs, axis = 0)    
#     # set up the other stuff
#     beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
#     beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
#     knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
#     beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
#     b0 = np.array(df.b0)
#     #counterfactual
#     qlist = []
#     for day in range(startpos, startpos+howfar):
#         X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
#         XB = X@beta_spline_coefs.T
#         sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + counterfactual[:,day])
#         S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#         Rt = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days        
#         qlist.append(Rt)
#     c_qmat = np.quantile(np.stack(qlist), [.025, .25, .5, .75, .975], axis = 1)


# plt.plot(b_qmat[2,:])
# plt.plot(c_qmat[2,:])
# plt.plot(mobarr[i,0,startpos:])
# plt.plot(arr_i[i,0,startpos:])
    
# deltavec = [-1, -.5, 0, .5, 1]
# mobarr = np.stack([np.stack(df[term]) for term in termlist])
# coefs = np.stack([df[f"mob_{term}"] for term in termlist])
# rep_coefs = np.stack([coefs for i in range(mobarr.shape[2])], axis = 2)
# termdict = {}

# arr_i = mobarr.copy()
# arr_i[5, :, startpos:(startpos+howfar)] = 0

# plt.plot(np.mean(mobarr[1,:,:(startpos+howfar)], axis = 0))
# plt.plot(np.mean(arr_i[1,:,:(startpos+howfar)], axis = 0))

# for mod_term in termlist:
#     qdict = {}
#     for dv in deltavec: 
#         qlist = []
#         arr_i = mobarr.copy()
#         # arr_i[[i for i in range(len(termlist)) if termlist[i] == mod_term][0], :, startpos:] += dv*arr_i[[i for i in range(len(termlist)) if termlist[i] == mod_term][0], :, startpos:]
#         arr_i[:5, :, startpos:] = 0
#         arr_i[5, :, startpos:] = 0
#         mob_effects = np.sum(arr_i * rep_coefs, axis = 0)
#         print(dv)
#         beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
#         beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
#         knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
#         beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
#         b0 = np.array(df.b0)
#         for day in range(startpos, startpos+howfar):
#             X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
#             XB = X@beta_spline_coefs.T
#             sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + mob_effects[:,day])
#             S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#             Rt = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days        
#             qlist.append(Rt)
#         qmat = np.stack(qlist)
#         qdict[dv] = np.quantile(qmat, [0.05,.25, 0.5, .75, 0.95], axis = 1)
#     termdict[mod_term] = qdict

# mod_term = termlist[2]
# qdict = termdict[mod_term]
# for i in list(qdict.keys()):
#     plt.plot(qdict[i][2,:], label = i)
# plt.legend()
# plt.title(mod_term)


# plt.plot(arr_i[1, 1, startpos:])

# plt.plot( np.quantile(qmat, [0.05,.25, 0.5, .75, 0.95], axis = 1)[2,])

# plt.hist(df[f"mob_{termlist[4]}"])


# mobdict['residential'].shape
# termval = 0

#     for dv in deltavec:
#         qlist = []
#         print(dv)
#         beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
#         beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
#         knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
#         beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
#         b0 = np.array(df.b0)
#         for day in range(startpos, startpos+howfar):
#             X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
#             XB = X@beta_spline_coefs.T
#             mob_effect = 0
#             for term in termlist:
#                 if (term == mod_term) and (day > startpos):
#                     mob_effect += dv*mobdict[term][:,day]*df[f'mob_{term}']
#                     print(f"{term}_{day}")
#                 else:
#                     mob_effect += mobdict[term][:,day]*df[f'mob_{term}']
#                     print(f"{term}_AAA_{day}")                    
#             sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + mob_effect)
#             S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#             Rt = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days
            
#         qdict[dv] = np.quantile(Rt, [0.05,.25, 0.5, .75, 0.95])

#     qdict[-0.1]


#     dates = pd.date_range(f"{first_day}", periods=howfar, freq="d")
#     qlist = []
#     qlist_beta, qlist_mob = [], []
#     if 'beta_spline_coef_0' in df.columns:
#         nobs = census_ts.shape[0]
#         beta_k = int(params.loc[params.param == 'beta_spline_dimension', 'base'])
#         beta_spline_power = int(params.loc[params.param == 'beta_spline_power', 'base'])
#         knots = np.linspace(0, nobs-nobs/beta_k/2, beta_k) # this has to mirror the knot definition in the _99_helper functons
#         beta_spline_coefs = np.array(df[[i for i in df.columns if 'beta_spline_coef' in i]])        
#         b0 = np.array(df.b0)
#         for day in range(nobs):
#             X = power_spline(day, knots, beta_spline_power, xtrim = nobs)
#             XB = X@beta_spline_coefs.T
#             mob_effect = df['mob_effect'].apply(lambda x: x[df.offset.iloc[0]+day])
#             sd = logistic(L = 1, k=1, x0 = 0, x=b0 + XB + mob_effect)
#             S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#             beta_t = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days
#             qlist.append(np.quantile(beta_t, [0.05,.25, 0.5, .75, 0.95]))
#             qlist_beta.append(np.quantile(b0 + XB, [0.05,.25, 0.5, .75, 0.95]))
#             qlist_mob.append(np.quantile(mob_effect, [0.05,.25, 0.5, .75, 0.95]))
#     else:        
#         for day in range(census_ts.shape[0]):
#             sd = logistic(
#                 df.logistic_L, df.logistic_k, df.logistic_x0 - df.offset.astype(int), day
#             )
#             S = df['s'].apply(lambda x: x[df.offset.iloc[0]+day])
#             beta_t = (df.beta * (1-sd)) * ((S/float(params.loc[params.param == "region_pop", 'base']))**df.nu)*df.recovery_days
#             qlist.append(np.quantile(beta_t, [0.05,.25, 0.5, .75, 0.95]))            
#     qmat = np.vstack(qlist)


# mobility forecast plots
def mobilitity_forecast_plot(df, census_ts, howfar, figdir, prefix):
    howfar = howfar+census_ts.shape[0]
    dates = pd.date_range(f"{census_ts.date.min()}", periods=howfar, freq="d")
    fig, ax = plt.subplots(nrows = 6, figsize=(8, 18))
    for i, term in enumerate(['retail_and_recreation', 'grocery_and_pharmacy', \
                              'parks', 'transit_stations', 'workplaces', \
                              'residential']):
        qmat = np.quantile(np.stack(df[term]), [0.05,.25, 0.5, .75, 0.95], axis = 0)
        ax[i].plot_date(dates[:len(census_ts[term])], census_ts[term], "-")
        ax[i].plot_date(dates, qmat[2,:howfar], "--")
        ax[i].fill_between(
            x=dates,
            y1=qmat[0, :howfar],
            y2=qmat[4, :howfar],
            alpha=0.3,
            lw=2,
            edgecolor="k",
        )
        ax[i].fill_between(
            x=dates,
            y1=qmat[1, :howfar],
            y2=qmat[3, :howfar],
            alpha=0.3,
            lw=2,
            edgecolor="k",
        )
        ax[i].set_xlabel("relative time spent")
        ax[i].title.set_text(term)
        ax[i].axhline(y = 0, color = "black")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path.join(f"{figdir}", f"{prefix}_mobility_prediction.pdf"))


def posterior_trace_plot(df, burn_in, figdir, prefix = ""):
    fig = plt.figure()
    for i in df.chain.unique():
        plt.plot(list(range(len(df.posterior.loc[df.chain == i]))),
                  df.posterior.loc[df.chain == i],
                  linewidth = .7)
    plt.axvline(x = burn_in, label = "burn-in")
    plt.ylabel("posterior")
    plt.xlabel("iteration")
    plt.legend()
    fig.savefig(path.join(f"{figdir}", f"{prefix}_posterior_trace.pdf"))


# def main():
#     p = ArgParser()
#     p.add("-c", "--my-config", is_config_file=True, help="config file path")
#     p.add(
#         "-o",
#         "--out",
#         help="output directory, '-' for stdin",
#         type=DirectoryType(),
#         required=True,
#     )
#     p.add(
#         "-a",
#         "--as_of",
#         default=0,
#         help="number of days in the past to project from",
#         type=int,
#     )
#     p.add("-y", "--y_max", help="max y-scale for the census graph", type=int)
#     p.add(
#         "-d",
#         "--n_days",
#         help="make a census/admits plot out to n_days",
#         type=int,
#         action="append",
#     )
#     p.add("-P", "--prefix", help="prefix for filenames")
#     p.add(
#         "-pp",
#         "--plot_pairs",
#         action="store_true",
#         help="Plot posterior samples in a pair-plot grid",
#     )
#     p.add(
#         "-pc",
#         "--plot_capacity",
#         action="store_true",
#         help="plot capacity as a horizontal line",
#     )
#     p.add(
#         "-b",
#         "--burn_in",
#         type=int,
#         help="how much of the burn-in to discard",
#         default = 2000
#     )

#     options = p.parse_args()
#     burn_in = options.burn_in
#     prefix = ""
#     if options.prefix is not None:
#         prefix = f"{options.prefix}_"

#     n_days = [30, 90, 180]
#     if options.n_days:
#         n_days = options.n_days

#     dir = options.out
#     print(f"Output directory: {dir}")
#     paramdir = path.join(dir, "parameters")
#     outdir = path.join(dir, "output")
#     figdir = path.join(dir, "figures")

#     census_ts, params, args = read_inputs(paramdir)
#     first_day = census_ts[census_ts.columns[0]].values[0] #weird chack for non-ascii characters in the input file

#     # TODO: This needs to be configurable based on the time period specificed
#     as_of_days_ago = args["as_of"]
#     nobs = census_ts.shape[0] - as_of_days_ago

#     # define capacity
#     vent_capacity, hosp_capacity = None, None
#     if options.plot_capacity:
#         vent_capacity = float(params.base.loc[params.param == "vent_capacity"])
#         hosp_capacity = float(params.base.loc[params.param == "hosp_capacity"])

# # df = pd.read_json("/Users/crandrew/projects/chime_sims/output/2020_05_08_20_38_34/output/chains.json.bz2", lines = True)
# # census_ts = pd.read_csv('/Users/crandrew/projects/chime_sims/output/2020_05_08_20_38_34/parameters/census_ts.csv')
# # params = pd.read_csv('/Users/crandrew/projects/chime_sims/output/2020_05_08_20_38_34/parameters/params.csv')

#     # Chains
#     df = pd.read_json(
#         path.join(f"{outdir}", "chains.json.bz2"), orient="records", lines=True
#     )
#     print(f"READ chains file: {df.shape[0]} total iterations")
#     # remove burn-in
    
#     iters_remaining = df.iter.max()-burn_in
#     assert iters_remaining>100, f"Breaking here: you are casting aside {burn_in} iterations as burn-in, but there are only {df.iter.max()} iteratons per chain"
#     if iters_remaining < 1000:
#         warnings.warn(f"You're only using {iters_remaining} iterations per chain.  This may not be fully cromulent.")
#     df = df.loc[(df.iter > burn_in)]

#     # make the social distancing plot
#     SD_plot(census_ts, params, df, figdir, prefix)
    
#     ##
#     for howfar in n_days:
#         plt_predictive(
#             df,
#             first_day,
#             census_ts,
#             figdir,
#             as_of_days_ago,
#             howfar=howfar,
#             prefix=prefix,
#             y_max=options.y_max,
#             hosp_capacity=hosp_capacity,
#             vent_capacity=vent_capacity,
#         )

#     mk_projection_tables(df, first_day, outdir)

#     toplot = df[
#         [
#             "beta",
#             "hosp_prop",
#             "ICU_prop",
#             "vent_prop",
#             "hosp_LOS",
#             "ICU_LOS",
#             "vent_LOS",
#             "incubation_days",
#             "recovery_days",
#             "logistic_k",
#             "logistic_x0",
#             "logistic_L",
#             "nu",
#         ]
#     ]

#     pspace = np.linspace(0.001, 0.999, 1000)

#     fig, ax = plt.subplots(figsize=(8, 40), ncols=1, nrows=len(toplot.columns))
#     for i in range(len(toplot.columns)):
#         cname = toplot.columns[i]
#         if params.loc[params.param == cname, "distribution"].iloc[0] == "gamma":
#             x = sps.gamma.ppf(
#                 pspace,
#                 params.loc[params.param == cname, "p1"],
#                 0,
#                 params.loc[params.param == cname, "p2"],
#             )
#             y = sps.gamma.pdf(
#                 x,
#                 params.loc[params.param == cname, "p1"],
#                 0,
#                 params.loc[params.param == cname, "p2"],
#             )
#         elif params.loc[params.param == cname, "distribution"].iloc[0] == "beta":
#             x = sps.beta.ppf(
#                 pspace,
#                 params.loc[params.param == cname, "p1"],
#                 params.loc[params.param == cname, "p2"],
#             )
#             y = sps.beta.pdf(
#                 x,
#                 params.loc[params.param == cname, "p1"],
#                 params.loc[params.param == cname, "p2"],
#             )
#         ax[i].plot(x, y, label="prior")
#         ax[i].hist(toplot[cname], density=True, label="posterior", bins=30)
#         ax[i].set_xlabel(params.loc[params.param == cname, "description"].iloc[0])
#         ax[i].legend()
#     plt.tight_layout()
#     fig.savefig(path.join(f"{figdir}", f"{prefix}marginal_posteriors_v2.pdf"))

#     if options.plot_pairs:
#         #  Make a pair plot for diagnosing posterior dependence
#         plt_pairplot_posteriors(toplot, figdir, prefix=prefix)


if __name__ == "__main__":
    main()
