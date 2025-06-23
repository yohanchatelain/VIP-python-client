import pandas as pd

from enigmatoolbox.datasets import load_summary_stats

enigma_subcortical_regions = [
    "Laccumb",
    "Lamyg",
    "Lcaud",
    "Lhippo",
    "Lpal",
    "Lput",
    "Lthal",
    "LLatVent",
    "Raccumb",
    "Ramyg",
    "Rcaud",
    "Rhippo",
    "Rpal",
    "Rput",
    "Rthal",
    "RLatVent",
]

enigma_cortical_regions = [
    "bankssts",
    "caudalanteriorcingulate",
    "caudalmiddlefrontal",
    "cuneus",
    "entorhinal",
    "fusiform",
    "inferiorparietal",
    "inferiortemporal",
    "isthmuscingulate",
    "lateraloccipital",
    "lateralorbitofrontal",
    "lingual",
    "medialorbitofrontal",
    "middletemporal",
    "parahippocampal",
    "paracentral",
    "parsopercularis",
    "parsorbitalis",
    "parstriangularis",
    "pericalcarine",
    "postcentral",
    "posteriorcingulate",
    "precentral",
    "precuneus",
    "rostralanteriorcingulate",
    "rostralmiddlefrontal",
    "superiorfrontal",
    "superiorparietal",
    "superiortemporal",
    "supramarginal",
    "frontalpole",
    "temporalpole",
    "transversetemporal",
    "insula",
]


class ENIGMAParser:

    _disorders = {
        "22q",
        "adhd",
        "asd",
        "bipolar",
        "depression",
        "epilepsy",
        "ocd",
        "schizophrenia",
    }
    _metrics = {"thickness", "area", "subcortical_volume"}
    _metric_to_column_mapping = {
        "22q": {
            "thickness": "CortThick_case_vs_controls",
            "area": "CortSurf_case_vs_controls",
            "subcortical_volume": "SubVol_case_vs_controls",
        },
        "adhd": {
            "thickness": "CortThick_case_vs_controls_adult",
            "area": "CortSurf_case_vs_controls_adult",
            "subcortical_volume": "SubVol_case_vs_controls_adult",
        },
        "asd": {
            "thickness": "CortThick_case_vs_controls_meta_analysis",
            "area": "CortSurf_case_vs_controls_meta_analysis",
            "subcortical_volume": "SubVol_case_vs_controls_meta_analysis",
        },
        "bipolar": {
            "thickness": "CortThick_case_vs_controls_adult",
            "area": "CortSurf_case_vs_controls_adult",
            "subcortical_volume": [
                "SubVol_case_vs_controls_typeI",
                "SubVol_case_vs_controls_typeII",
            ],
        },
        "epilepsy": {
            "thickness": [
                "CortThick_case_vs_controls_allepilepsy",
                "CortThick_case_vs_controls_gge",
                "CortThick_case_vs_controls_rtle",
                "CortThick_case_vs_controls_ltle",
                "CortThick_case_vs_controls_allotherepilepsy",
            ],
            "subcortical_volume": [
                "SubVol_case_vs_controls_allepilepsy",
                "SubVol_case_vs_controls_gge",  # idiopathic generalized epilepsies
                "SubVol_case_vs_controls_rtle",  # right MTLE with right hippocampal sclerosis
                "SubVol_case_vs_controls_ltle",  # left MTLE with left hippocampal sclerosis
                "SubVol_case_vs_controls_allotherepilepsy",
            ],
        },
        "depression": {
            "thickness": "CortThick_case_vs_controls_adult",
            "area": "CortSurf_case_vs_controls_adult",
            "subcortical_volume": "SubVol_case_vs_controls",
        },
        "ocd": {
            "thickness": "CortThick_case_vs_controls_adult",
            "area": "CortSurf_case_vs_controls_adult",
            "subcortical_volume": "SubVol_case_vs_controls_adult",
        },
        "schizophrenia": {
            "thickness": "CortThick_case_vs_controls",
            "area": "CortSurf_case_vs_controls",
            "subcortical_volume": "SubVol_case_vs_controls",
        },
    }

    def _assert_disorder(self, disorder):
        if disorder not in self._disorders:
            raise ValueError(
                f"Disorder '{disorder}' is not supported. Supported disorders are: {self._disorders}"
            )
        return disorder

    def _assert_metric(self, metric):
        if metric not in self._metrics:
            raise ValueError(
                f"Metric '{metric}' is not supported. Supported metrics are: {self._metrics}"
            )
        return metric

    def __init__(self, disorder, metric):
        self.disorder = self._assert_disorder(disorder)
        self.metric = self._assert_metric(metric)

    def get_subgroup_from_column_name(self, column_name):
        fields = column_name.split("case_vs_controls")[-1].split("_")[1:]
        return "_".join(fields) if fields else "all"

    def load_summary_stats(self):
        """
        Load ENIGMA summary statistics.

        Parameters:
        - subcortical: Boolean indicating whether to load subcortical regions.

        Returns:
        - DataFrame containing the summary statistics in ENIGMA format.
        """
        if self.metric not in self._metric_to_column_mapping[self.disorder]:
            return None

        summary_stats = {
            "disorder": self.disorder,
            "metric": self.metric,
            "subgroup": [],
            "statistics": [],
        }
        data = load_summary_stats(self.disorder)
        column_names = self._metric_to_column_mapping[self.disorder][self.metric]
        if isinstance(column_names, list):
            for col in column_names:
                subgroup = self.get_subgroup_from_column_name(col)
                summary_stats["subgroup"].append(subgroup)
                summary_stats["statistics"].append(data[col])
        else:
            subgroup = self.get_subgroup_from_column_name(column_names)
            summary_stats["subgroup"].append(subgroup)
            summary_stats["statistics"].append(data[column_names])

        return summary_stats


class GeneralParser:
    """
    General parser for ENIGMA summary statistics.
    This class is a base class for specific parsers like ENIGMAParser and LivingParkParser.
    """

    def __init__(self, disorder, metric, filename):
        self.disorder = disorder
        self.metric = metric
        self.filename = filename
        self.data = None

    def _assert_cortical_regions(self):
        regions_lateralized = [
            hemisphere + "_" + region
            for hemisphere in ["L", "R"]
            for region in enigma_cortical_regions
        ]
        regions = self.data["Structure"]
        if not regions.isin(regions_lateralized).all():
            regions_missing = set(regions_lateralized) - set(regions)
            raise ValueError(f"Data is missing cortical regions: {regions_missing}")

    def _assert_subcortical_regions(self):
        regions = self.data["Structure"]
        if not regions.isin(enigma_subcortical_regions).all():
            regions_missing = set(enigma_subcortical_regions) - set(regions)
            raise ValueError(f"Data is missing subcortical regions: {regions_missing}")

    def _assert_data(self):
        if "Structure" not in self.data.columns:
            raise ValueError("Data must contain 'Structure' column.")
        if "Cohen_d" not in self.data.columns:
            raise ValueError("Data must contain 'Cohen_d' column.")
        if self.metric == "thickness" or self.metric == "area":
            self._assert_cortical_regions()
        elif self.metric == "subcortical_volume":
            self._assert_subcortical_regions()
        else:
            raise ValueError(
                f"Metric '{self.metric}' is not supported. Supported metrics are: 'thickness', 'area', 'subcortical_volume'."
            )

    def load_summary_stats(self):
        self.data = pd.read_csv(self.filename)
        self._assert_data()

        summary_stats = {
            "disorder": self.disorder,
            "metric": self.metric,
            "subgroup": ["all"],
            "statistics": [self.data],
        }

        return summary_stats


class LivingParkParser:

    _subcortical_regions_enigma_mapping = {
        "Left-Accumbens-area": "Laccumb",
        "Left-Amygdala": "Lamyg",
        "Left-Caudate": "Lcaud",
        "Left-Hippocampus": "Lhippo",
        "Left-Pallidum": "Lpal",
        "Left-Putamen": "Lput",
        "Left-Thalamus": "Lthal",
        "Left-Lateral-Ventricle": "LLatVent",
        "Right-Accumbens-area": "Raccumb",
        "Right-Amygdala": "Ramyg",
        "Right-Caudate": "Rcaud",
        "Right-Hippocampus": "Rhippo",
        "Right-Pallidum": "Rpal",
        "Right-Putamen": "Rput",
        "Right-Thalamus": "Rthal",
        "Right-Lateral-Ventricle": "RLatVent",
    }

    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def convert_region_to_enigma_format(self, data, subcortical=False):
        """
        Convert data to ENIGMA format.

        Parameters:
        - data: DataFrame containing the data to be converted.

        Returns:
        - DataFrame in ENIGMA format.
        """
        # Assuming 'data' is a pandas DataFrame
        # Prefix the region names with 'L' or 'R' for left and right hemispheres
        if subcortical:
            data["region"] = data["region"].apply(
                lambda x: self._subcortical_regions_enigma_mapping.get(x, x)
            )
        else:
            data["region"] = data[["hemisphere", "region"]].apply(
                lambda x: (
                    "L_" + x[1]
                    if "lh" in x[0]
                    else "R_" + x[1] if "rh" in x[0] else x[1]
                ),
                axis=1,
            )
        data = data.rename(columns={"region": "Structure"})
        return data

    def load_summary_stats(self, subcortical=False):
        """
        Load LivingPark summary statistics.

        Parameters:
        - subcortical: Boolean indicating whether to load subcortical regions.

        Returns:
        - DataFrame containing the summary statistics in LivingPark format.
        """
        # Placeholder for actual implementation
        data = pd.read_csv(self.filename)
        self.data = self.convert_region_to_enigma_format(data, subcortical=subcortical)
        return self.data
