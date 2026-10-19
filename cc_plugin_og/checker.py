import datetime
from typing import ClassVar

import requests
from compliance_checker.base import BaseCheck, BaseNCCheck, Result

from cc_plugin_og import __version__


class OGChecker(BaseNCCheck):
    _cc_spec = "og"
    _cc_url = "https://oceangliderscommunity.github.io/OG-format-user-manual/OG_Format.html"
    _cc_author = "Rob Cermak, Callum Rollo"
    _cc_checker_version = __version__
    _cc_spec_version = "1.0"
    _cc_description = f"og {_cc_spec_version} compliance-checker"
    _cc_display_headers: ClassVar[dict[int, str]] = {
        3: "Mandatory",
        2: "Highly Recommended",
        1: "Suggested",
    }

    def __init__(self):
        pass

    @classmethod
    def beliefs(cls):
        return {}

    @classmethod
    def make_result(cls, level, score, out_of, name, messages):
        return Result(level, (score, out_of), name, messages)

    def setup(self, ds):
        """
        Set up the OG checker by assigning the dataset

        **No validation of the attribute is performed.**

        Parameters
        ----------
        ds : netCDF4 dataset object
        """

        self.ds = ds

    def check_dimensions(self, ds):
        """
        Check for mandatory dimensions
        """
        level = BaseCheck.HIGH
        score = 0
        messages = []
        desc = "Check for mandatory dimensions."
        required_dims = [
            "N_MEASUREMENTS",
        ]
        out_of = len(required_dims)

        for dimension in required_dims:
            test = dimension in ds.dimensions
            score += int(test)
            if not test:
                messages.append(f"Dimension {dimension} is missing")

        return self.make_result(level, score, out_of, desc, messages)

    def check_mandatory_variables(self, ds):
        """
        Check for mandatory variables.
        """

        level = BaseCheck.HIGH
        score = 0
        messages = []
        desc = "Check for mandatory variables."

        required_variables = [
            "LATITUDE_GPS",
            "LONGITUDE_GPS",
            "TIME_GPS",
            "LATITUDE",
            "LONGITUDE",
            "TIME",
            "DEPTH",
            "TRAJECTORY",
            "PLATFORM_MODEL",
            "WMO_IDENTIFIER",
            "PLATFORM_SERIAL_NUMBER",
            "DEPLOYMENT_TIME",
            "DEPLOYMENT_LATITUDE",
            "DEPLOYMENT_LONGITUDE",
        ]

        out_of = len(required_variables)

        for variable in required_variables:
            test = variable in ds.variables
            score += int(test)
            if not test:
                messages.append(f"Variable {variable} is missing")

        return self.make_result(level, score, out_of, desc, messages)

    def check_attribute_names_are_lowercase(self, ds):
        """
        Check that all attribute names are lowercase.
        """

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 0
        messages = []
        desc = "Check that all attribute names are lowercase."

        # Check global attributes
        attr_exceptions = ["Conventions", "featureType"]
        for attr in ds.ncattrs():
            if attr in attr_exceptions:
                continue
            out_of += 1
            test = attr.lower()
            if test != attr:
                messages.append(
                    f"Global attribute {attr} should be lowercase: {test}",
                )
            else:
                score += 1

        # Check variable attributes
        # Skip [masked, masked_array] variable attributes
        attr_exceptions = ["_FillValue"]
        for variable in ds.variables:
            for attr in ds.variables[variable].ncattrs():
                if attr in attr_exceptions:
                    continue
                out_of += 1
                if not isinstance(attr, str):
                    msg = f"Expected str, got {type(attr)}."
                    raise TypeError(msg)

                test = attr.lower()
                if test != attr:
                    messages.append(
                        f"Variable {variable} attribute {attr} should be lowercase: {test}",
                    )
                else:
                    score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_variable_names_are_capitalized(self, ds):
        """
        Check that variable names are capitalized.
        """

        level = BaseCheck.MEDIUM
        score = 0
        out_of = len(ds.variables)
        messages = []
        desc = "Variable names should be capitalized."

        for variable in ds.variables:
            test = variable.upper()
            if test != variable:
                messages.append(
                    f"Variable {variable} should be capitalized: {test}",
                )
            else:
                score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_mandatory_global_attributes(self, ds):
        """
        Check for mandatory global attributes.
        """

        level = BaseCheck.HIGH
        score = 0
        messages = []
        desc = "Check for mandatory global attributes."

        required_attributes = [
            "title",
            "platform",
            "platform_vocabulary",
            "id",
            "contributor_name",
            "contributor_email",
            "contributor_role",
            "contributor_role_vocabulary",
            "contributing_institutions",
            "contributing_institutions_role",
            "contributing_institutions_role_vocabulary",
            "rtqc_method",
            "start_date",
            "date_created",
            "featureType",
            "Conventions",
        ]

        out_of = len(required_attributes)
        for attribute in required_attributes:
            test = attribute in ds.ncattrs()
            score += int(test)
            if not test:
                messages.append(f"Global attribute {attribute} is missing")

        return self.make_result(level, score, out_of, desc, messages)

    def check_sensors(self, ds):
        """
        Check that all sensors referred to in variables are present.
        """
        level = BaseCheck.HIGH
        score = 0
        messages = []
        sensors = []
        desc = "sensors referred to in variables should be present"
        for variable in ds.variables:
            attrs = ds.variables[variable].ncattrs()
            if "sensor" in attrs:
                sensors.append(ds.variables[variable].getncattr("sensor"))

        sensors = set(sensors)
        out_of = len(sensors)

        for sensor in sensors:
            test = sensor in ds.variables
            if not test:
                messages.append(f"Sensor variable {sensor} is missing")
            else:
                score += int(test)

        return self.make_result(level, score, out_of, desc, messages)

    def check_dates(self, ds):
        """
        Check that all dates in metadata are correctly formatted
        """
        level = BaseCheck.HIGH
        score = 0
        messages = []
        desc = "dates should be formatted as YYYYmmddTHHMMss"

        dates_to_check = [
            "start_date",
            "date_created",
            "time_coverage_start",
            "time_coverage_end",
        ]
        attrs = ds.ncattrs()
        dates = set(dates_to_check).intersection(attrs)
        out_of = len(dates)

        for date_name in dates:
            date_str = ds.getncattr(date_name)
            try:
                datetime.datetime.strptime(date_str, "%Y%m%dT%H%M%S%z")
                score += 1
            except ValueError:
                messages.append(
                    f"Date {date_name}: {date_str} is not formatted as YYYYmmddTHHMMss",
                )

        return self.make_result(level, score, out_of, desc, messages)

    def check_variables_og1_url(self, ds):
        """
        Check that variable names are capitalized.
        """
        og1_collection = requests.get(
            "https://vocab.nerc.ac.uk/collection/OG1/current/?_profile=nvs&_mediatype=application/ld+json",
        ).json()
        graph = og1_collection["@graph"]
        concepts = graph[:-1]
        og1_uri_list = [concept["@id"] for concept in concepts]
        level = BaseCheck.HIGH
        score = 0
        out_of = len(ds.variables)
        messages = []
        desc = "Variables should have valid vocabulary URIs"

        for var_name in ds.variables:
            variable = ds.variables[var_name]
            if (
                variable.dimensions != ("N_MEASUREMENTS",)
                or var_name[-3:] == "_QC"
            ):
                score += 1
                continue
            attrs = variable.ncattrs()
            if "vocabulary" not in attrs:
                messages.append(
                    f"variable {var_name} should have attribute 'vocabulary', value is a URI from the OG1 collection",
                )
                continue
            uri = variable.getncattr("vocabulary")
            if "https" in uri:
                messages.append(
                    f"variable {var_name} vocabulary {uri} contains https. Vocabulary URIs use http",
                )
                continue
            if uri[-1] != "/":
                messages.append(
                    f"variable {var_name} vocabulary {uri} should end with a forward slash '/'",
                )
                continue
            if uri not in og1_uri_list:
                messages.append(
                    f"variable {var_name} vocabulary {uri} not found in NERC OG1 collection",
                )
                continue
            if "long_name" not in attrs:
                messages.append(
                    f"variable {var_name} should have attribute 'long_name'",
                )
                continue
            score += 1

        return self.make_result(level, score, out_of, desc, messages)
