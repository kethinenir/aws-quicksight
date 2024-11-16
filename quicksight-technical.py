# 1. Set up AWS environment and permissions
import boto3
import json

# IAM role for QuickSight
quicksight_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "athena:StartQueryExecution",
                "athena:GetQueryResults"
            ],
            "Resource": ["arn:aws:s3:::your-bucket/*", "arn:aws:athena:*"]
        }
    ]
}

# 2. Set up Glue Crawler
def create_glue_crawler():
    glue = boto3.client('glue')
    response = glue.create_crawler(
        Name='sales_data_crawler',
        Role='AWSGlueServiceRole',
        DatabaseName='sales_db',
        Targets={
            'S3Targets': [
                {'Path': 's3://your-bucket/sales-data/'}
            ]
        },
        Schedule='cron(0 0 * * ? *)'  # Run daily at midnight
    )
    return response

# 3. Create QuickSight Dataset
def create_quicksight_dataset():
    quicksight = boto3.client('quicksight')
    
    # Physical table definition
    physical_table = {
        "RelationalTable": {
            "DataSourceArn": "arn:aws:quicksight:region:account:datasource/source-id",
            "Schema": "sales_db",
            "Name": "sales_table",
            "InputColumns": [
                {"Name": "sale_date", "Type": "DATETIME"},
                {"Name": "product_id", "Type": "STRING"},
                {"Name": "quantity", "Type": "INTEGER"},
                {"Name": "revenue", "Type": "DECIMAL"}
            ]
        }
    }
    
    # Logical table with transformations
    logical_table = {
        "Alias": "sales_analysis",
        "DataTransforms": [
            {
                "CreateColumnsOperation": {
                    "Columns": [
                        {
                            "ColumnName": "unit_price",
                            "ColumnId": "unit_price",
                            "Expression": "revenue / quantity"
                        }
                    ]
                }
            }
        ]
    }
    
    response = quicksight.create_data_set(
        AwsAccountId='your-account-id',
        DataSetId='sales_dataset',
        Name='Sales Analysis Dataset',
        PhysicalTableId='sales_table',
        LogicalTableMap={'sales_table': logical_table},
        ImportMode='SPICE',
        RefreshSchedule={
            'Schedule': 'cron(0 0 * * ? *)',
            'RefreshType': 'INCREMENTAL_REFRESH',
            'IncrementalRefreshProperties': {
                'LookbackWindow': 1,
                'LookbackWindowUnit': 'DAYS'
            }
        }
    )
    return response

# 4. Create Analysis and Visuals
def create_analysis():
    quicksight = boto3.client('quicksight')
    
    # Define sheet with visuals
    sheet_definition = {
        "Visuals": [
            {
                "LineChartVisual": {
                    "Title": {"Visible": True, "Text": "Sales Trend"},
                    "XAxis": {"FieldId": "sale_date"},
                    "YAxis": {"FieldId": "revenue"},
                    "Legend": {"Visible": True, "Position": "RIGHT"},
                    "DataLabels": {"Visible": True},
                    "Actions": [
                        {
                            "ActionOperations": [
                                {
                                    "DrillDownOperation": {
                                        "TargetVisual": "product_details"
                                    }
                                }
                            ],
                            "Triggers": ["CLICK"]
                        }
                    ]
                }
            }
        ]
    }
    
    response = quicksight.create_analysis(
        AwsAccountId='your-account-id',
        AnalysisId='sales_analysis',
        Name='Sales Analysis',
        Definition=sheet_definition,
        Permissions=[
            {
                'Principal': 'arn:aws:quicksight:region:account:user/default/user1',
                'Actions': ['quicksight:DescribeAnalysis', 'quicksight:UpdateAnalysis']
            }
        ]
    )
    return response

# 5. Publish Dashboard
def publish_dashboard():
    quicksight = boto3.client('quicksight')
    
    response = quicksight.create_dashboard(
        AwsAccountId='your-account-id',
        DashboardId='sales_dashboard',
        Name='Sales Dashboard',
        Permissions=[
            {
                'Principal': 'arn:aws:quicksight:region:account:group/default/analysts',
                'Actions': [
                    'quicksight:DescribeDashboard',
                    'quicksight:ListDashboardVersions',
                    'quicksight:QueryDashboard'
                ]
            }
        ],
        SourceEntity={
            'SourceTemplate': {
                'DataSetReferences': [
                    {
                        'DataSetPlaceholder': 'sales_data',
                        'DataSetArn': 'arn:aws:quicksight:region:account:dataset/sales_dataset'
                    }
                ],
                'Arn': 'arn:aws:quicksight:region:account:template/sales_template'
            }
        },
        VersionDescription='Initial version'
    )
    return response

# 6. Generate Embedding URL
def get_dashboard_url():
    quicksight = boto3.client('quicksight')
    
    response = quicksight.get_dashboard_embed_url(
        AwsAccountId='your-account-id',
        DashboardId='sales_dashboard',
        IdentityType='IAM',
        SessionLifetimeInMinutes=600,
        UndoRedoDisabled=False,
        ResetDisabled=False
    )
    return response['EmbedUrl']
