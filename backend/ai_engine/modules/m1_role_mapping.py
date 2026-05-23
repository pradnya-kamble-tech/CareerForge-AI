# m1_role_mapping.py — Data Understanding & Role Mapping (Module 1)
# Identifies, standardizes, and encodes all job role categories from the dataset.

import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_PATH = os.path.join(_BASE_DIR, "data", "resume_dataset.csv")

# Standardize raw category names
_CATEGORY_MAP = {
    "HR": "HR",
    "Designer": "Designer",
    "Information-Technology": "Information Technology",
    "Teacher": "Teacher",
    "Advocate": "Advocate",
    "Business-Development": "Business Development",
    "Healthcare": "Healthcare",
    "Fitness": "Fitness",
    "Agriculture": "Agriculture",
    "BPO": "BPO",
    "Sales": "Sales",
    "Consultant": "Consultant",
    "Digital-Media": "Digital Media",
    "Automobile": "Automobile",
    "Chef": "Chef",
    "Finance": "Finance",
    "Apparel": "Apparel",
    "Engineering": "Engineering",
    "Accountant": "Accountant",
    "Construction": "Construction",
    "Public-Relations": "Public Relations",
    "Banking": "Banking",
    "Arts": "Arts",
    "Aviation": "Aviation",
}

# Role icons for frontend display
_ROLE_ICONS = {
    "HR": "HR", "Designer": "DS", "Information Technology": "IT",
    "Teacher": "TC", "Advocate": "AD", "Business Development": "BD",
    "Healthcare": "HC", "Fitness": "FT", "Agriculture": "AG",
    "BPO": "BP", "Sales": "SL", "Consultant": "CN",
    "Digital Media": "DM", "Automobile": "AU", "Chef": "CH",
    "Finance": "FN", "Apparel": "AP", "Engineering": "EN",
    "Accountant": "AC", "Construction": "CO", "Public Relations": "PR",
    "Banking": "BK", "Arts": "AR", "Aviation": "AV",
}

_DOMAIN_MAP = {
    # Engineering / IT -> TECHNICAL
    "Information Technology": "TECHNICAL",
    "Engineering": "TECHNICAL",
    "Automobile": "TECHNICAL",
    "Construction": "TECHNICAL",
    # HR / Business / Management -> BUSINESS
    "HR": "BUSINESS",
    "Business Development": "BUSINESS",
    "Sales": "BUSINESS",
    "Consultant": "BUSINESS",
    "Public Relations": "BUSINESS",
    "BPO": "BUSINESS",
    # Arts / Design -> CREATIVE
    "Designer": "CREATIVE",
    "Digital Media": "CREATIVE",
    "Arts": "CREATIVE",
    "Apparel": "CREATIVE",
    # Education -> EDUCATION
    "Teacher": "EDUCATION",
    # Health / Fitness -> HEALTHCARE
    "Healthcare": "HEALTHCARE",
    "Fitness": "HEALTHCARE",
    # Finance -> FINANCE
    "Finance": "FINANCE",
    "Accountant": "FINANCE",
    "Banking": "FINANCE",
    # Others -> OPERATIONS
    "Advocate": "LEGAL",
    "Chef": "OPERATIONS",
    "Agriculture": "OPERATIONS",
    "Aviation": "OPERATIONS",
}

def get_domain_for_role(role_name):
    """Return the broad domain for a given role category."""
    return _DOMAIN_MAP.get(role_name, "DEFAULT")


def load_dataset():
    """Load the Kaggle resume dataset and standardize categories."""
    df = pd.read_csv(_DATA_PATH)
    df["Category_Clean"] = df["Category"].map(_CATEGORY_MAP).fillna(df["Category"])
    return df


def get_role_labels():
    """Return the sorted list of 25 standardized role labels."""
    # Use actual dataset values to prevent unseen label errors
    df = load_dataset()
    return sorted(df["Category_Clean"].unique().tolist())


def get_role_icon(role_name):
    """Return the 2-char icon for a role."""
    return _ROLE_ICONS.get(role_name, role_name[:2].upper())


def get_label_encoder():
    """Fit and return a LabelEncoder on all dataset role labels."""
    le = LabelEncoder()
    le.fit(get_role_labels())
    return le


def get_role_distribution():
    """Return a dict of {role: count} from the dataset."""
    df = load_dataset()
    dist = df["Category_Clean"].value_counts().to_dict()
    return dist


def get_category_map():
    """Return the raw→clean category mapping."""
    return dict(_CATEGORY_MAP)
