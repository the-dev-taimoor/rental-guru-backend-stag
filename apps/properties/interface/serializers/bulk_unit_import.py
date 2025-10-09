import pandas as pd
from io import BytesIO
from rest_framework import serializers
from collections import defaultdict

from common.constants import Error
from apps.properties.infrastructure.models import  Property
from apps.properties.exceptions import CustomValidationError
from apps.properties.utils import xlsx_sheet_names, COLUMN_CONFIG

from common.utils import snake_case, str_to_bool

class BulkUnitImportSerializer(serializers.Serializer):
    property = serializers.IntegerField(required=True)
    file = serializers.FileField(required=True)

    def validate(self, attrs):
        if not attrs['file'].name.endswith('.xlsx'):
            raise CustomValidationError("File must be in XLSX format")

        property_instance = Property.objects.get(id=attrs['property'])
        property_type_ = property_instance.property_type
        key = 'others'
        if property_type_ == 'university_housing':
            xlsx_sheet_names_ = xlsx_sheet_names['university_housing']
            key = 'university_housing'
        else:
            xlsx_sheet_names_ = xlsx_sheet_names['others']

        try:
            file_data = attrs['file'].read()
            xls = pd.ExcelFile(BytesIO(file_data))

            # Validate sheet presence
            found_sheets = set(xls.sheet_names)
            required_sheets = set(xlsx_sheet_names_.keys())
            missing_sheets = required_sheets - found_sheets
            if missing_sheets:
                raise CustomValidationError(f"Missing sheets: {', '.join(missing_sheets)}")

            data = self.process_excel_data(xls, key)
            data['property'] = attrs['property']

            # Process all column transformations
            for section in COLUMN_CONFIG:
                if section in data:
                    self.process_section(data, section)

            return data

        except Exception as e:
            raise CustomValidationError(e)

    def process_excel_data(self, xls, key):
        """Process all sheets from Excel file into structured data"""
        if key == 'university_housing':
            number_col_uq = 'Room Number'
            sheet_name_uq = 'Room Details'
        else:
            number_col_uq = 'Unit Number'
            sheet_name_uq = 'Unit Info'
        all_data = {}

        for sheet_name, expected_columns in xlsx_sheet_names[key].items():
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                df.columns = df.columns.str.strip()

                # Validate columns
                missing_cols = set(expected_columns) - set(df.columns)
                if missing_cols:
                    raise CustomValidationError(f"Missing columns in {sheet_name}: {', '.join(missing_cols)}")

                # Process data
                sheet_data = defaultdict(list)
                for _, row in df.iterrows():
                    unit_key = snake_case(row[number_col_uq])
                    row_data = {expected_columns[col]: row[col] for col in df.columns if col in expected_columns}
                    sheet_data[unit_key].append(row_data)

                all_data[snake_case(sheet_name)] = dict(sheet_data)

                # Checking if photos are present for all units
                unit_df = pd.read_excel(xls, sheet_name=sheet_name_uq)
                unit_df.columns = unit_df.columns.str.strip()

                unit_numbers = unit_df[number_col_uq].tolist()
                unit_info_keys = set(unit_numbers)

                photo_df = pd.read_excel(xls, sheet_name='Photos')
                photo_df.columns = photo_df.columns.str.strip()
                photo_unit_numbers = set(photo_df[number_col_uq].tolist())

                units_without_photos = unit_info_keys - photo_unit_numbers
                if units_without_photos:
                    raise CustomValidationError(Error.PHOTO_REQUIRED_FOR_UNIT.format(', '.join(units_without_photos)))

            except Exception as e:
                raise CustomValidationError(f"Error in sheet {sheet_name}: {str(e)}")

        return all_data

    def process_section(self, data, section_name):
        """Generic method to process any section based on COLUMN_CONFIG"""
        config = COLUMN_CONFIG.get(section_name, {})
        if not config or section_name not in data:
            return

        for unit, items in data[section_name].items():
            if not items:
                continue

            # Iterate over each item in the list of the current unit
            for item in items:
                updates = {}
                for field, (target_field, target_value) in config["fields"].items():
                    if field in item and str_to_bool(item[field]):
                        updates[target_field] = target_value

                # Apply updates to the item if any
                if updates:
                    item.update(updates)

                # After updating, remove the original fields
                for field in config["fields"]:
                    if field in item:
                        del item[field]