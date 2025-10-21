from io import BytesIO

import pandas as pd
from rest_framework import serializers

from apps.user_management.infrastructure.models import VendorInvitation
from common.exceptions import CustomValidationError
from common.utils import snake_case


class BulkVendorInviteSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate(self, attrs):
        if not (attrs['file'].name.endswith('.xlsx') or attrs['file'].name.endswith('.csv')):
            raise CustomValidationError("File must be in CSV/XLSX format")

        try:
            file_data = attrs['file'].read()
            if attrs['file'].name.endswith('.xlsx'):
                xls = pd.ExcelFile(BytesIO(file_data))
                df = pd.read_excel(xls, sheet_name=0)
            else:
                df = pd.read_csv(BytesIO(file_data), skip_blank_lines=True)
            df.dropna(how='all', inplace=True)

            df.columns = df.columns.str.strip()
            expected_columns = ['First Name', 'Last Name', 'Email', 'Role']
            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                raise CustomValidationError(f"Missing columns: {', '.join(missing_cols)}")

            data = []
            for _, row in df.iterrows():
                role_ = snake_case(row['Role'])
                vendor_data = {'first_name': row['First Name'], 'last_name': row['Last Name'], 'email': row['Email'], 'role': role_}
                if role_ not in dict(VendorInvitation.VENDOR_ROLE_CHOICES):
                    raise CustomValidationError(f"Invalid role: {row['Role']}")
                data.append(vendor_data)

            return data

        except Exception as e:
            raise CustomValidationError(e)
