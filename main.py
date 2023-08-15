import argparse
import boto3
import yaml
import os


def read_credentials(file_path):
    with open(file_path, 'r') as file:
        credentials = yaml.safe_load(file)
        access_key_id = credentials['access_key_id']
        secret_access_key = credentials['secret_access_key']
        session_token = credentials['session_token']
        region = credentials['region']
    return access_key_id, secret_access_key, session_token, region


def list_vpcs(ec2_client):
    print("Existing VPCs:")
    vpcs = list(ec2_client.vpcs.all())
    for i, vpc in enumerate(vpcs, 1):
        print(f"{i}. VPC ID: {vpc.id}, CIDR Block: {vpc.cidr_block}")
    print()


def create_vpc(friendly_name, vpc_cidr, subnet_cidr, access_key_id, secret_access_key, session_token, region):
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )

        ec2_client = session.client('ec2')

        # Create VPC
        vpc_response = ec2_client.create_vpc(CidrBlock=vpc_cidr)
        vpc_id = vpc_response['Vpc']['VpcId']

        # Add Name tag to VPC
        ec2_client.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': f"{friendly_name}-vpc"}])

        # Create Internet Gateway
        ig_response = ec2_client.create_internet_gateway()
        internet_gateway_id = ig_response['InternetGateway']['InternetGatewayId']
        ec2_client.create_tags(Resources=[internet_gateway_id], Tags=[{'Key': 'Name', 'Value': f"{friendly_name}-ig"}])

        # Attach Internet Gateway to VPC
        ec2_client.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=internet_gateway_id)

        # Create Route Table
        route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        ec2_client.create_tags(Resources=[route_table_id], Tags=[{'Key': 'Name', 'Value': f"{friendly_name}-rt"}])

        # Create Subnet
        subnet_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=subnet_cidr)
        subnet_id = subnet_response['Subnet']['SubnetId']
        ec2_client.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': f"{friendly_name}-subnet"}])

        print("VPC and associated resources created successfully.")
    except Exception as e:
        print("An error occurred:", str(e))


def get_user_choice():
    print("Choose an option:")
    print("1. List existing VPCs")
    print("2. Create a new VPC")
    print("3. Quit")

    while True:
        choice = input("Enter your choice: ")
        if choice in ['1', '2', '3']:
            return choice
        print("Invalid choice. Please try again.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AWS VPC Creation Script')
    parser.add_argument('--name', help='Friendly name for the VPC and associated resources')
    parser.add_argument('--vpc-cidr', help='CIDR block for the VPC')
    parser.add_argument('--subnet-cidr', help='CIDR block for the subnet')
    args = parser.parse_args()

    credentials_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.yaml')

    if os.path.exists(credentials_file):
        access_key_id, secret_access_key, session_token, region = read_credentials(credentials_file)
        if args.name and args.vpc_cidr and args.subnet_cidr:
            create_vpc(args.name, args.vpc_cidr, args.subnet_cidr, access_key_id, secret_access_key, session_token, region)
        else:
            while True:
                choice = get_user_choice()
                if choice == '1':
                    session = boto3.Session(
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key,
                        aws_session_token=session_token,
                        region_name=region
                    )
                    ec2_client = session.resource('ec2')
                    list_vpcs(ec2_client)
                elif choice == '2':
                    name = input("Enter the friendly name for the VPC and associated resources: ")
                    vpc_cidr = input("Enter the CIDR block for the VPC (e.g., 10.0.0.0/16): ")
                    subnet_cidr = input("Enter the CIDR block for the subnet (e.g., 10.0.0.0/24): ")
                    create_vpc(name, vpc_cidr, subnet_cidr, access_key_id, secret_access_key, session_token, region)
                elif choice == '3':
                    print("Script execution terminated.")
                    break
    else:
        print("Credentials file not found. Please make sure 'credentials.yaml' exists in the script directory.")
