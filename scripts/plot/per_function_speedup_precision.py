import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.patches as mpatches
import sys
from plot.plotting_utilities import *
import argparse

this_directory = os.path.dirname(os.path.realpath(__file__)) + "/"
this_filename = sys.argv[0].split('/')[-1]

project_dir = this_directory + '../../'

parser = argparse.ArgumentParser(description='Generate the figure of the run time breakdown.',
                                 usage='python {} -i results/'.format(this_filename))

parser.add_argument('-i', '--inputdir', type=str, default=os.path.join(project_dir, 'results'),
                    help='The directory with the results.')

parser.add_argument('-c', '--cases', type=str, default='lhc,sps,ps',
                    help='A comma separated list of the testcases to run. Default: lhc,sps,ps')

parser.add_argument('-s', '--show', action='store_true',
                    help='Show the plots.')
parser.add_argument('-e', '--errorbars', action='store_true',
                    help='Add errorbars.')


args = parser.parse_args()
args.cases = args.cases.split(',')

res_dir = args.inputdir
images_dir = os.path.join(res_dir, 'plots')

if not os.path.exists(images_dir):
    os.makedirs(images_dir)

gconfig = {
    'approx': {
        '0': 'exact',
        '1': 'SRP',
        '2': 'RDS',
    },
    'hatches': ['//', '\\', ''],
    'markers': ['x', 'o', '^'],
    'colors': {'f32': 'xkcd:teal', 'f64': 'xkcd:peach'},
    'edgecolors': ['xkcd:red', 'xkcd:blue'],
    'x_name': 'function',
    # 'x_to_keep': [4, 8, 16, 32, 64],
    # 'omp_name': 'omp',
    'y_name': 'total_time(sec)',
    'xlabel': 'Functions',
    'ylabel': r'Norm. Runtime',
    'title': {
        # 's': '{}'.format(),
        'fontsize': 10,
        # 'y': .82,
        # 'x': 0.55,
        'fontweight': 'bold',
    },
    'figsize': [6, 2.2],
    'annotate': {
        'fontsize': 9,
        'textcoords': 'data',
        'va': 'bottom',
        'ha': 'center'
    },
    'ticks': {'fontsize': 10},
    'fontsize': 10,
    'legend': {
        'loc': 'upper right', 'ncol': 1, 'handlelength': 1.5, 'fancybox': False,
        'framealpha': 0.8, 'fontsize': 10, 'labelspacing': 0, 'borderpad': 0.5,
        'handletextpad': 0.5, 'borderaxespad': 0.1, 'columnspacing': 0.8,
        # 'bbox_to_anchor': (0., 0.85)
    },
    'subplots_adjust': {
        'wspace': 0.1, 'hspace': 0.1,
        # 'top': 0.93
    },
    'tick_params_left': {
        'pad': 1, 'top': 0, 'bottom': 1, 'left': 1,
        'direction': 'out', 'length': 3, 'width': 1,
    },
    'tick_params_center_right': {
        'pad': 1, 'top': 0, 'bottom': 1, 'left': 0,
        'direction': 'out', 'length': 3, 'width': 1,
    },
    'fontname': 'DejaVu Sans Mono',
    'phases': ['comm', 'serial'],
    'ylim': [0, 1.2],
    'xlim': [1.6, 36],
    'yticks': [0, 20, 40, 60, 80, 100],
    'outfiles': ['{}/{}-{}.png', '{}/{}-{}.pdf'],
    'files': [
        '{}/{}/precision-monitor/avg-report.csv',
        # '{}/{}/lb-tp-approx1-strong-scaling/comm-comp-report.csv',
    ],
    'lines': {
        # 'mpi': ['mpich3', 'mvapich2', 'openmpi3'],
        'prec': ['single', 'double'],
        # 'type': ['comm', 'comp', 'serial', 'other'],
    },
    'categories': {
        'LIKick': ['comp:LIKick'],
        'kick': ['comp:kick'],
        'drift': ['comp:drift'],
        'histo': ['comp:histo'],
        'indVolt': ['serial:InductiveImped', 'serial:beam_spectrum_gen',
                    'serial:indVolt1Turn'],
        'updateImp': ['serial:updateImp'],
        'total': ['total_time']
        # 'beamFB': ['serial:PSBBeamFB', 'serial:beam_phase', 'serial:phase_difference']
    },

    # 'color': {
    #     'LIkick': ['comp:LIkick'],
    #     'kick': ['comp:kick'],
    #     'drift': ['comp:drift'],
    #     'histo': ['comp:histo'],
    #     'indVolt': ['serial:InductiveImped', 'serial:beam_spectrum_gen',
    #     'serial:indVolt1Turn'],
    #     'updateImp': ['serial:updateImp'],
    #     'beamFB': ['serial:PSBBeamFB', 'serial:beam_phase', 'serial:phase_difference']

    # }

}

plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True  # Let TeX do the typsetting
# Force sans-serif math mode (for axes labels)
plt.rcParams['text.latex.preamble'] = [r'\usepackage{sansmath}', r'\sansmath']
plt.rcParams['font.family'] = 'sans-serif'  # ... for regular text
plt.rcParams['font.sans-serif'] = 'Helvetica'

# plt.rcParams['font.family'] = gconfig['fontname']
# plt.rcParams['text.usetex'] = True

if __name__ == '__main__':
    for col, case in enumerate(args.cases):
        print('[{}] tc: {}: {}'.format(
            this_filename[:-3], case, 'Reading data'))

        # ax = ax_arr[col]
        # plt.sca(ax)
        plots_dir = {}
        for file in gconfig['files']:
            file = file.format(res_dir, case)
            # print(file)
            data = np.genfromtxt(file, delimiter='\t', dtype=str)
            header, data = list(data[0]), data[1:]
            temp = get_plots(header, data, gconfig['lines'],
                             exclude=gconfig.get('exclude', []),
                             prefix=True)
            for key in temp.keys():
                plots_dir['_{}'.format(key)] = temp[key].copy()

        fig, ax = plt.subplots(ncols=1, nrows=1,
                               sharex=True, sharey=True,
                               figsize=gconfig['figsize'])
        # ax_arr = ax_arr.ravel()

        final_dir = {}
        for idx, k in enumerate(plots_dir.keys()):
            # ax = ax_arr[idx]
            # plt.sca(ax)
            # other = 100.
            if 'single' in k:
                precision = 'f32'
            elif 'double' in k:
                precision = 'f64'
            if precision not in final_dir:
                final_dir[precision] = {}

            for row in plots_dir[k]:
                func = row[header.index(gconfig['x_name'])]
                for cat, subcat in gconfig['categories'].items():
                    if func in subcat:
                        if cat not in final_dir[precision]:
                            final_dir[precision][cat] = 0
                        final_dir[precision][cat] += float(
                            row[header.index(gconfig['y_name'])])
                        # other -= float(row[header.index(gconfig['y_name'])])
                # phase = key.split('_type')[1].split('_')[0]
                # k = key.split('_type')[0]
                # if k not in final_dir:
                #     final_dir[k] = {}
                # if phase not in final_dir[k]:
                #     final_dir[k][phase] = plots_dir[key].copy()
            # final_dir['other'] = other

        step = 1
        width = step/3
        pos = 0
        xticks = []
        labels = set()
        for cat in gconfig['categories'].keys():
            offset = 0
            for prec in ['f64', 'f32']:
                # for k, v in final_dir[]
                if prec not in labels:
                    label = prec
                    labels.add(label)
                else:
                    label = None
                val = final_dir[prec][cat] / final_dir['f64'][cat]
                plt.bar(pos+offset, val, width=.9*width,
                        edgecolor='0', color=gconfig['colors'][prec],
                        label=label)
                ax.annotate('{:.2f}'.format(val), xy=(pos+offset, val),
                            **gconfig['annotate'])
                offset += width
            xticks.append(cat)
            pos += step

            # plt.pie(final_dir.values(), labels=final_dir.keys(),
            #         explode=[0.01]*len(final_dir),
            #         autopct='%1.1f', pctdistance=0.8,
            #         labeldistance=1.1)
            # ax.axis('equal')
        plt.title(f'{case.upper()}-f32/f64 Speedup', **gconfig['title'])

        plt.ylim(gconfig['ylim'])
        plt.ylabel(gconfig['ylabel'], labelpad=2, color='xkcd:black',
               fontsize=gconfig['fontsize'])
        plt.xlabel(gconfig['xlabel'], labelpad=2, color='xkcd:black',
               fontsize=gconfig['fontsize'])

        plt.xticks(np.arange(pos)+width/2, xticks, **gconfig['ticks'])
        plt.legend(**gconfig['legend'])

        plt.tight_layout()

        # plt.subplots_adjust(**gconfig['subplots_adjust'])
        for file in gconfig['outfiles']:
            file = file.format(
                images_dir, this_filename[:-3], '-'.join(args.cases))
            print('[{}] {}: {}'.format(this_filename[:-3], 'Saving figure', file))
            save_and_crop(fig, file, dpi=600, bbox_inches='tight')
        if args.show:
            plt.show()
        plt.close()

        # plt.grid(True, which='major', alpha=0.5, zorder=1)
        # plt.grid(False, which='major', axis='x')
        # plt.title('{}'.format(case.upper()), **gconfig['title'])
        # if col == 1:
        #     plt.xlabel(gconfig['xlabel'], labelpad=3,
        #                fontweight='bold',
        #                fontsize=gconfig['fontsize'])
        # if col == 0:
        #     plt.ylabel(gconfig['ylabel'], labelpad=3,
        #                fontweight='bold',
        #                fontsize=gconfig['fontsize'])

        # pos = 0
        # step = 1
        # width = 0.85 * step / (len(final_dir.keys()))
        # print('[{}] tc: {}: {}'.format(
        #     this_filename[:-3], case, 'Plotting data'))

        # for idx, k in enumerate(final_dir.keys()):
        #     approx = k.split('approx')[1].split('_')[0]
        #     approx = gconfig['approx'][approx]
        #     label = '{}'.format(approx)
        #     labels.add(label)
        #     bottom = []
        #     # colors = gconfig['colors'][idx]
        #     j = 0
        #     for phase in gconfig['phases']:

        #         values = final_dir[k][phase]
        #     # for phase, values in final_dir[k].items():
        #         y = get_values(values, header, gconfig['y_name'])
        #         x = get_values(values, header, gconfig['x_name'])
        #         omp = get_values(values, header, gconfig['omp_name'])
        #         if phase == 'serial':
        #             y += get_values(final_dir[k]['other'],
        #                             header, gconfig['y_name'])

        #         # x_new = []
        #         # y_new = []
        #         # for i, xi in enumerate(gconfig['x_to_keep']):
        #         #     # if xi in x:
        #         #     x_new.append(xi)
        #         #     y_new.append(y[list(x).index(xi)])
        #         # x = np.array(x_new)
        #         # y = np.array(y_new)
        #         x = x * omp[0] // 20
        #         if len(bottom) == 0:
        #             bottom = np.zeros(len(y))

        #         plt.bar(np.arange(len(x)) + pos, y, bottom=bottom, width=0.9*width,
        #                 label=None,
        #                 linewidth=1.5,
        #                 edgecolor=gconfig['edgecolors'][idx],
        #                 hatch=gconfig['hatches'][idx],
        #                 color=gconfig['colors'][j],
        #                 zorder=2)
        #         j += 1
        #         bottom += y
        #     pos += width
        # plt.xticks(np.arange(len(x))+step/4,
        #            np.array(x, int), **gconfig['ticks'])

        # plt.ylim(gconfig['ylim'])
        # plt.xlim(0-width, len(x))
        # if col == 0:
        #     ax.tick_params(**gconfig['tick_params_left'])
        # else:
        #     ax.tick_params(**gconfig['tick_params_center_right'])

        # plt.xticks(**gconfig['ticks'])
        # plt.yticks(gconfig['yticks'], gconfig['yticks'], **gconfig['ticks'])

        # if col == 0:
        #     handles = []
        #     for c, p in zip(gconfig['colors'], ['comm', 'intra', 'other']):
        #         patch = mpatches.Patch(label=p, edgecolor='black', facecolor=c,
        #                                linewidth=1.,)
        #         handles.append(patch)

        #     for h, tc, e in zip(gconfig['hatches'], labels, gconfig['edgecolors']):
        #         patch = mpatches.Patch(label=tc, edgecolor=e,
        #                                facecolor='1', hatch=h, linewidth=1.5,)
        #         handles.append(patch)
        #     plt.legend(handles=handles, **gconfig['legend'])
