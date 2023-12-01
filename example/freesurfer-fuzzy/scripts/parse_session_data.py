import json
import argparse
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import scipy
from plotly.subplots import make_subplots

class Collect:
    '''
    Class to collect_missing data
    - visit -> dict: local: list of repetitions where visit is missing
    - visit -> dict: remote: list of repetitions where visit is missing

    '''
    def __init__(self):
        self.local = {}
        self.remote = {}

    def add_local(self, visit, rep):
        if visit not in self.local:
            self.local[visit] = []
        self.local[visit].append(rep)

    def add_remote(self, visit, rep):
        if visit not in self.remote:
            self.remote[visit] = []
        self.remote[visit].append(rep)

    def get_local(self, visit):
        return self.local.get(visit, [])

    def get_remote(self, visit):
        return self.remote.get(visit, [])

    def get_visits(self):
        return set(self.local.keys()) | set(self.remote.keys())

    def get_local_visits(self):
        return set(self.local.keys())

    def get_remote_visits(self):
        return set(self.remote.keys())

    def get_local_reps(self, visit):
        return self.local.get(visit, [])

    def get_remote_reps(self, visit):
        return self.remote.get(visit, [])

    def get_local_reps_count(self, visit):
        return len(self.local.get(visit, []))

    def get_remote_reps_count(self, visit):
        return len(self.remote.get(visit, []))

    def get_local_visits_count(self):
        return len(self.local)

    def get_remote_visits_count(self):
        return len(self.remote)    
    
    def get_local_count_of_rep(self, rep):
        counter = 0
        for visit, reps in self.local.items():
            if rep in reps:
                counter += 1
        return counter

    def get_remote_count_of_rep(self, rep):
        counter = 0
        for visit, reps in self.remote.items():
            if rep in reps:
                counter += 1
        return counter

collect_present = Collect()
collect_missing = Collect()

def read_json(filename):
    with open(filename, 'r') as fi:
        return json.load(fi)
    raise FileNotFoundError(filename)

def load_subjects(filename):
    subjects = read_json(filename)
    if "first_visit" in subjects:
        return subjects["first_visit"]
    if "PATNO_id" in subjects:
        return subjects["PATNO_id"]
    if "visit" in subjects:
        return subjects["visit"]
    raise Exception("Cannot find subjects")

def print_header(data):
    session_name = data['session_name']
    pipeline_id = data['pipeline_id']
    local_input_dir = data['local_input_dir']
    local_output_dir = data['local_output_dir']
    vip_input_dir = data['vip_input_dir']
    vip_output_dir = data['vip_output_dir']
    input_settings = data['input_settings']

    print("session_name:", session_name)
    print("pipeline_id:", pipeline_id)
    print("local_input_dir:", local_input_dir)
    print("local_output_dir:", local_output_dir)
    print("vip_input_dir:", vip_input_dir)
    print("vip_output_dir:", vip_output_dir)
    print("input_settings:")
    for name, v in input_settings.items():
        print(name, v)

def get_real_start(outputs):
    starts = set()
    for elt in outputs:
        name = elt['path']
        dirname = os.path.dirname(name).split(os.path.sep)[-1]
        starts.add(dirname)
    return starts

def get_remote_visits(outputs):
    return [os.path.basename(elt['path']) for elt in outputs]

def parse_date(date_string):
    return datetime.strptime(date_string, "%d-%m-%Y_%H:%M:%S")

def print_workflow_info(name, v, total):
    outputs = v['outputs']
    archive_paths = get_remote_visits(outputs)
    start = v['real_start']        
    size = len(outputs)
    missings = total - size
    print(f"name={name}, start={start}, present={size:03}/{total:03}, missings={missings:03}")

def get_local_visits(local_output_dir):
    local_archive = set()
    for root, dirs, files in os.walk(local_output_dir):
        for name in files:
            if name.endswith('.tgz'):
                local_archive.add(name)
    return local_archive

def filter_visit_names(visits):
    visits_filtered = []
    for visit in visits:
        basename = os.path.basename(visit)
        visit = basename.split('.')[0]
        visits_filtered.append(visit)
    return visits_filtered

def check_against_local_archive(remote_visits, local_visits, reference_visits, repetition):
    remote_visits = filter_visit_names(remote_visits)
    local_visits = filter_visit_names(local_visits)
    reference_visits = filter_visit_names(reference_visits)

    total_visits = len(reference_visits)

    for reference_visit in reference_visits:
        if reference_visit not in remote_visits:
            # print(f"\treference_visit={reference_visit} not in remote_visits")
            collect_missing.add_remote(reference_visit, repetition)
        else:
            collect_present.add_remote(reference_visit, repetition)
        if reference_visit not in local_visits:
            # print(f"\treference_visit={reference_visit} not in local_visits")
            collect_missing.add_local(reference_visit, repetition)
        else:
            collect_present.add_local(reference_visit, repetition)
            
    local_visits_count = collect_missing.get_local_count_of_rep(repetition)
    remote_visits_count = collect_missing.get_remote_count_of_rep(repetition)

    local_missing_ratio = local_visits_count/total_visits*100
    remote_missing_ratio = remote_visits_count/total_visits*100
    
    print(f"Missing {local_visits_count:3}  local visits ({local_missing_ratio:.2f}%)")
    print(f"Missing {remote_visits_count:3} remote visits ({remote_missing_ratio:.2f}%)")
    

def print_missing_visits(collect_missing):
    local_visits = collect_missing.get_local_visits()
    remote_visits = collect_missing.get_remote_visits()
    total_visits = len(local_visits) + len(remote_visits)
    local_visits_count = collect_missing.get_local_visits_count()
    remote_visits_count = collect_missing.get_remote_visits_count()
    local_missing_ratio = local_visits_count/total_visits*100
    remote_missing_ratio = remote_visits_count/total_visits*100
    print(f"Missing {local_visits_count:3}  local visits ({local_missing_ratio:.2f}%)")
    print(f"Missing {remote_visits_count:3} remote visits ({remote_missing_ratio:.2f}%)")

def print_number_missing_per_visit(collect_missing):
    visits = collect_missing.get_visits()
    for visit in visits:
        local_count = collect_missing.get_local_reps_count(visit)
        remote_count = collect_missing.get_remote_reps_count(visit)
        if local_count < remote_count:
            print(f"visit={visit}, local={local_count}, remote={remote_count}")
        # print(f"visit={visit}, local={local_count}, remote={remote_count}")

def get_number_missing_per_visit(collect_missing):
    visits = collect_missing.get_visits()
    local_counts = []
    remote_counts = []
    for visit in visits:
        local_counts.append(collect_missing.get_local_reps_count(visit))
        remote_counts.append(collect_missing.get_remote_reps_count(visit))
    return local_counts, remote_counts

def get_number_present_per_visit(collect_present):
    visits = collect_present.get_visits()
    local_counts = []
    remote_counts = []
    for visit in visits:
        local_counts.append(collect_present.get_local_reps_count(visit))
        remote_counts.append(collect_present.get_remote_reps_count(visit))
    return local_counts, remote_counts

def plot_missing_per_visit(collect_missing):
    '''
    Use plotly to plot the distribution of missing visits for local and remote
    '''
    local_counts, remote_counts = get_number_missing_per_visit(collect_missing)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=local_counts, name='local'))
    fig.add_trace(go.Histogram(x=remote_counts, name='remote'))
    fig.update_layout(title="Number of missing visits per repetition", xaxis_title="Number of missing visits", yaxis_title="Number of repetitions")
    fig.show()

def plot_present_per_visit(collect_present):
    '''
    Use plotly to plot the distribution of missing visits for local and remote
    '''
    local_counts, remote_counts = get_number_present_per_visit(collect_present)
    fig = go.Figure()

    local_hist, local_bin_edges = np.histogram(local_counts, bins=len(set(local_counts))-1)
    remote_hist, remote_bin_edges = np.histogram(remote_counts, bins=len(set(remote_counts))-1)

    local_inverse_cumulative = np.flip(np.cumsum(np.flip(local_hist)))
    remote_inverse_cumulative = np.flip(np.cumsum(np.flip(remote_hist)))

    local_bin_starts = local_bin_edges[:-1]
    local_bin_ends = local_bin_edges[1:]

    remote_bin_starts = remote_bin_edges[:-1]
    remote_bin_ends = remote_bin_edges[1:]

    fig.add_trace(go.Bar(
        x=[f"{int(end)}" for start, end in zip(local_bin_starts, local_bin_ends)],
        y=local_inverse_cumulative,
        name='local',
        legendgroup='count',
        legendgrouptitle_text="count",
    ))
    fig.add_trace(go.Bar(
        x=[f"{int(end)}" for start, end in zip(remote_bin_starts, remote_bin_ends)],
        y=remote_inverse_cumulative,
        name='remote',
        legendgroup='count',
        legendgrouptitle_text="count",
    ))
    fig.add_trace(go.Bar(
        x=[f"{int(end)}" for start, end in zip(local_bin_starts, local_bin_ends)],
        y=local_inverse_cumulative/local_inverse_cumulative.max(),
        name='local',
        legendgroup='ratio',
        legendgrouptitle_text="ratio",
    ))
    fig.add_trace(go.Bar(
        x=[f"{int(end)}" for start, end in zip(remote_bin_starts, remote_bin_ends)],
        y=remote_inverse_cumulative/remote_inverse_cumulative.max(),
        name='remote',
        legendgroup='ratio',
        legendgrouptitle_text="ratio",

    ))

    fig.update_layout(title="Number of visits with at least n repetitions", xaxis_title="n", yaxis_title="Number of visits")
    fig.show()

def plot_heatmap_cnh():
    '''
    Use plotly to plot the function log(x)/log(y) for x in [0.5,1] and y in [0.5,1]
    Plot contours for log(x)/log(y) = i, for i in 1...13
    1/2 log2( (n-1) / chi2_{1-alpha/2} ) + log2( F^{-1}( (p+1) / 2) )
    '''

    sizes = [7,8,9,10]
    
    fig = make_subplots(cols=2, rows=2, subplot_titles=[f"n={n}" for n in sizes])

    i = 1    

    for n in sizes:

        (row, col) = ((i+1)//2 , i%2 + 1)

        alpha = np.linspace(0.5, 0.999, 100)
        p = np.linspace(0.5, 0.999, 100)
        
        chi2 = scipy.stats.chi2.interval(1-alpha/2, n - 1)[0]
        inorm = scipy.stats.norm.ppf((p + 1) / 2)
        Z = 0.5 * np.log2((n - 1) / chi2) + np.log2(inorm)
        
        contour = go.Contour(z=Z, x=p, y=alpha, colorscale='Bluered')
        fig.add_trace(contour, row=row, col=col)
        fig.update_layout(title='delta', xaxis_title='p', yaxis_title='1-α')
        fig.update_xaxes(gridcolor='black', griddash='dash', minor_griddash="dot")
        fig.update_yaxes(gridcolor='black', griddash='dash', minor_griddash="dot")
        fig.update_traces(line_width=2, selector=dict(type='contour'))

        i += 1
        
    fig.show()

def plot_heatmap():
    '''
    Use plotly to plot the function log(x)/log(y) for x in [0.5,1] and y in [0.5,1]
    Plot contours for log(x)/log(y) = i, for i in 1...13
    '''
    
    alpha = np.linspace(0.5, 0.999, 100)
    p = np.linspace(0.5, 0.999, 100)
    Z = np.log(1-alpha)/np.log(p)
    fig = go.Figure(data=[go.Contour(z=Z, x=p, y=alpha, contours=dict(start=1, end=13, size=1, showlabels=True), line_smoothing=0.01, contours_coloring='lines', colorscale='Bluered')])
    fig.update_layout(title='log(1-α)/log(p)', xaxis_title='p', yaxis_title='1-α')
    fig.update_xaxes(gridcolor='black', griddash='dash', minor_griddash="dot")
    fig.update_yaxes(gridcolor='black', griddash='dash', minor_griddash="dot")
    fig.update_traces(line_width=2, selector=dict(type='contour'))
    fig.show()

def plot_stats_from_nsamples(n):
    '''
    Use plotly to plot the function log(x)/log(y) for x in [0.5,1] and y in [0.5,1]
    Plot function 0 = log(x)/log(y) - n <-> y = exp(log(x)/n)
    '''
    alpha = np.linspace(0.001, 0.5, 100)
    fig = go.Figure()

    for i in range(7, 14):
        z = np.exp(np.log(alpha)/i)
        fig.add_trace(go.Scatter(x=alpha, y=z, name=i))
    
    fig.update_layout(title=f'n=log(α)/log(p)', xaxis_title='α', yaxis_title='p')
    fig.show()

def print_workflows(data, subjects: dict[str, str]):

    workflows_counter = 0
    total = len(subjects)
    
    real_starts_set = set()
    workflows = data['workflows']

    workflows_filtered = {}
    
    for name, v in workflows.items():
        outputs = v['outputs']
        start = v['start']
        size = len(outputs)
        missings = total - size
        real_starts = get_real_start(outputs)
        real_starts_set.update(real_starts)
        real_start = real_starts.pop() if real_starts else None
        v['real_start'] = real_start
        if real_start and size > 10 and not real_start.startswith('07-07-2023'):
            workflows_filtered[name] = v.copy()

    workflows_sorted = sorted(workflows_filtered.items(), key=lambda i: parse_date(i[1]['real_start']))
    for rep, i in enumerate(workflows_sorted, start=1):
        print(f"rep{rep}")
        name, v = i
        outputs = v['outputs']
        reference_visits = set(subjects.values())
        remote_visits = get_remote_visits(outputs)
        local_visits = get_local_visits(f'rep{rep}/.archive/')
        check_against_local_archive(remote_visits, local_visits, reference_visits, repetition=rep)
        workflows_counter += 1

    print("workflows_counter:", workflows_counter)


def parse_args():
    parser = argparse.ArgumentParser("info session_data.json")
    parser.add_argument("--filename", default='session_data.json')
    parser.add_argument("--subjects-json", required=True, help="JSON subjects file to compare against")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    subjects = load_subjects(args.subjects_json)
    data = read_json(args.filename)
    print_header(data)
    print_workflows(data, subjects)
    print_missing_visits(collect_missing)
    print_number_missing_per_visit(collect_missing)
    plot_missing_per_visit(collect_missing)
    plot_present_per_visit(collect_present)
    plot_heatmap()
    plot_heatmap_cnh()
    plot_stats_from_nsamples(10)
    
if '__main__' == __name__:
    main()
