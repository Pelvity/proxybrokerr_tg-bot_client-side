import asyncio
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from typing import List, Tuple
from .proxyServiceInterface import ProxyServiceInterface
import logging
import io
import zipfile
import pandas as pd
from aiohttp import web
import requests
import json
import subprocess
from aiohttp.web import Response

from src.config.config import MEGA_LOGIN, MEGA_PASSWORD

class TrafficDataService:
    def __init__(self, proxy_service: ProxyServiceInterface, sender_email: str, sender_password: str, recipient_email: str):
        self.proxy_service = proxy_service
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email

    async def send_email_with_attachments(self, subject: str, body: str, attachments: List[Tuple[str, bytes]]):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        for attachment_name, attachment_data in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_name}"')
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        text = msg.as_string()
        server.sendmail(self.sender_email, self.recipient_email, text)
        server.quit()
        

# Assuming other necessary imports and class definitions are present

    async def generate_monthly_traffic_report(self, year: int, month: int, max_retries: int = 1):
        logging.info(f"Generating monthly traffic report for {year}-{month}")
        
        last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)
        first_day_of_month = datetime(year, month, 1)

        user_connections = await self.proxy_service.getAllProxies()
        logging.info(f"Retrieved {len(user_connections)} user connections")

        result_data = []

        for connection in user_connections:
            connection_id = connection.id
            logging.info(f"Processing connection: {connection_id}")

            # Tariff processing
            tariff_message = connection.tariff_plan
            if "BigDaddy Pro" in tariff_message:
                tariff_price = "10"
            elif "BigDaddy" in tariff_message:
                tariff_price = "8"
            else:
                tariff_price = "N/A"

            total_tx_bytes = 0
            total_rx_bytes = 0
            most_used_service = "N/A"

            zip_directory = "zip_files"
            os.makedirs(zip_directory, exist_ok=True)  # Create the directory if it doesn't exist

            month_name = first_day_of_month.strftime("%B")
            zip_filename = f"{connection_id}-{first_day_of_month.strftime('%Y%m%d')}_{last_day_of_month.strftime('%Y%m%d')}-logs-{month_name}.zip"
            zip_file_path = os.path.join(zip_directory, zip_filename)

            retry_count = 0
            with zipfile.ZipFile(zip_file_path, "w") as zip_file:
                current_date = first_day_of_month
                while current_date <= last_day_of_month:
                    interval_end_date = min(current_date + timedelta(days=6), last_day_of_month)
                    # Subtract 2 hours from the current_date to start from approximately 22:00
                    from_timestamp = int((current_date - timedelta(hours=2)).timestamp() * 1000)
                    # Adjust the to_timestamp to extend a few minutes into the next day
                    to_timestamp = int((interval_end_date + timedelta(days=1, minutes=5) - timedelta(milliseconds=1)).timestamp() * 1000)

                    logging.info(f"Fetching traffic data for {connection_id} from {current_date} to {interval_end_date}")
                    interval_tx_bytes, interval_rx_bytes, interval_most_used_service, csv_data, error_message = await self.proxy_service.getTrafficData(connection_id, from_timestamp, to_timestamp)
                    
                    if error_message:
                        retry_count += 1
                        if retry_count >= max_retries:
                            logging.error(f"Skipping connection {connection_id} after {max_retries} retries")
                            break
                        else:
                            logging.warning(f"Retry {retry_count} for connection {connection_id}")
                            continue

                    total_tx_bytes += interval_tx_bytes
                    total_rx_bytes += interval_rx_bytes
                    if most_used_service == "N/A":
                        most_used_service = interval_most_used_service

                    csv_filename = f"{connection_id}-{current_date.strftime('%Y%m%d')}_{interval_end_date.strftime('%Y%m%d')}.csv"
                    
                    # Check if csv_data is not empty
                    if not csv_data:
                        logging.warning(f"CSV data is empty for connection {connection_id} from {current_date} to {interval_end_date}")
                    else:
                        # Write the CSV data to a temporary file
                        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                            temp_file.write(csv_data)
                            temp_file_path = temp_file.name
                            temp_file.close()  # Make sure to close the file
                        
                        # Add the temporary file to the zip file
                        zip_file.write(temp_file_path, arcname=csv_filename)
                        
                        # Remove the temporary file
                        os.remove(temp_file_path)

                    current_date = interval_end_date + timedelta(days=1)

            if retry_count < max_retries:
                total_data_gb = (total_tx_bytes + total_rx_bytes) / (1024 * 1024 * 1024)

                days_in_period = (last_day_of_month - first_day_of_month).days + 1
                avg_data_gb_per_day = total_data_gb / days_in_period

                connection_data = {
                    "Description": connection.user,
                    "Connection Name": connection.name.split(" - ")[0],
                    "Total Data (GB)": f"{total_data_gb:.2f}",
                    "Avg Data (GB/day)": f"{avg_data_gb_per_day:.2f}",
                    "Most Used Service": most_used_service,
                    "Tariff": tariff_price
                }
                result_data.append(connection_data)

                try:
                    # Assuming upload_to_mega function exists and works as expected
                    download_link = await upload_to_mega(zip_file_path, connection_id, MEGA_LOGIN, MEGA_PASSWORD)
                    logging.info(f"Zip file uploaded to Mega.nz: {zip_filename}")
                except Exception as e:
                    logging.error(f"Failed to upload zip file to Mega.nz: {str(e)}")

                logging.info(f"Monthly traffic report generated for connection {connection_id}")

                # Delete all the zip files downloaded from iproxy for the current connection
                for file in os.listdir(zip_directory):
                    if file.startswith(f"{connection_id}-") and file.endswith("-logs.zip") and "-logs-" not in file:
                        iproxy_zip_file_path = os.path.join(zip_directory, file)
                        try:
                            os.remove(iproxy_zip_file_path)
                            logging.info(f"Zip file downloaded from iproxy deleted: {file}")
                        except Exception as e:
                            logging.error(f"Failed to delete zip file downloaded from iproxy: {file}. Error: {str(e)}")

        logging.info(f"Monthly traffic report generated for all connections")
        print(result_data)
        return result_data




        
import subprocess
import logging
import os

from mega import Mega
import tempfile

async def upload_to_mega(zip_file_path: str, connection_id: str, email: str, password: str) -> str:
    try:
        # Create a Mega.nz client instance
        mega = Mega()

        # Login to Mega.nz
        m = mega.login(email, password)

        # Find or create the "iproxy_logs" folder
        iproxy_logs_folder = m.find("iproxy_logs")
        if not iproxy_logs_folder:
            iproxy_logs_folder = m.create_folder("iproxy_logs")
        else:
            iproxy_logs_folder = iproxy_logs_folder[0]

        # Find the connection ID folder inside "iproxy_logs"
        #connection_folder = m.find(connection_id, iproxy_logs_folder)
        connection_folder = m.find(connection_id, exclude_deleted=True)

        # If the connection ID folder doesn't exist, create it
        if not connection_folder:
            connection_folder = m.create_folder(connection_id, iproxy_logs_folder)
        else:
            connection_folder = connection_folder[0]

        # Upload the zip file to the connection ID folder
        file = m.upload(zip_file_path, connection_folder)

        # Get the download link for the uploaded file
        download_link = m.get_upload_link(file)

        return download_link

    except Exception as e:
        logging.error(f"An error occurred while uploading zip file to Mega.nz: {str(e)}")
        raise e




 
def parse_timestamp(timestamp):
    formats = [
        '%Y-%m-%d %H:%M:%S.%f %z UTC',
        '%Y-%m-%d %H:%M:%S %z UTC'
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(timestamp, format=fmt)
        except ValueError:
            pass
    
    return pd.NaT

async def process_interval_data(connection_id: str, interval_zip_data: bytes, zip_buffer: io.BytesIO):
    zip_file = zipfile.ZipFile(io.BytesIO(interval_zip_data))
    csv_file = zip_file.open(zip_file.namelist()[0])
    interval_data = pd.read_csv(csv_file)

    interval_data['TimestampMillis'] = interval_data['TimestampMillis'].apply(parse_timestamp)

    # Convert datetime values to UTC and remove timezone information
    interval_data['TimestampMillis'] = interval_data['TimestampMillis'].dt.tz_convert('UTC').dt.tz_localize(None)

    # Create a ZipFile object using the BytesIO object
    with zipfile.ZipFile(zip_buffer, mode='a') as zip_output:
        # Group the data by day and save each day's data as a separate CSV file in the zip buffer
        for day_date, day_data in interval_data.groupby(pd.Grouper(key='TimestampMillis', freq='D')):
            csv_filename = f"{connection_id}-{day_date.strftime('%Y%m%d')}.csv"
            csv_buffer = io.StringIO()
            day_data.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode('utf-8')
            zip_output.writestr(csv_filename, csv_data)

""" async def divide_zip_file(zip_data: bytes, max_size: int, connection_id: str, first_day_of_month: datetime, last_day_of_month: datetime) -> List[Tuple[str, bytes]]:
    zip_parts = []
    part_num = 1
    start = 0
    while start < len(zip_data):
        end = start + max_size
        part_data = zip_data[start:end]
        part_name = f"{connection_id}-{first_day_of_month.strftime('%Y%m%d')}_{last_day_of_month.strftime('%Y%m%d')}-logs-part{part_num}.zip"
        
        # Create a new zip file for each part
        with zipfile.ZipFile(io.BytesIO(part_data), 'w') as zip_file:
            zip_file.writestr(f"{connection_id}-{first_day_of_month.strftime('%Y%m%d')}_{last_day_of_month.strftime('%Y%m%d')}-logs.csv", part_data)
        
        zip_parts.append((part_name, zip_file.getvalue()))
        start = end
        part_num += 1
    return zip_parts """

""" from mega import Mega
upload_to_megasync def a(zip_data: bytes, attachment_name: str) -> str:
    mega = Mega()
    m = mega.login(MEGA_PASSWORD, MEGA_LOGIN)
    folder = m.find("TrafficLogs")  # Find or create a folder named "TrafficLogs"
    if not folder:
        folder = m.create_folder("TrafficLogs")
    file = m.upload(zip_data, folder[0], attachment_name)
    download_link = m.get_upload_link(file)
    return download_link """

""" async def process_interval_data(connection_id: str, interval_zip_data: bytes, zip_buffer: io.BytesIO):
    zip_file = zipfile.ZipFile(io.BytesIO(interval_zip_data))
    csv_file = zip_file.open(zip_file.namelist()[0])
    interval_data = pd.read_csv(csv_file)

    # Convert 'TimestampMillis' column to datetime using the custom parsing function
    interval_data['TimestampMillis'] = interval_data['TimestampMillis'].apply(parse_timestamp)

    for day_date, day_data in interval_data.groupby(pd.Grouper(key='TimestampMillis', freq='D')):
        day_filename = f"{connection_id}-{day_date.strftime('%Y%m%d')}-logs.csv"
        day_data.to_csv(day_filename, index=False)

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(day_filename, day_filename)

        os.remove(day_filename) """
        










