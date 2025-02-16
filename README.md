# Google Sheets API Service

A FastAPI service to interact with Google Spreadsheets using the gspread library. This service exposes RESTful endpoints for listing spreadsheets, managing worksheets, and performing CRUD operations on cells, rows, and columns.

This version uses a base64-encoded Google Service Account JSON stored in an environment variable, so you don't need to mount the file in your container.

## Features

- **Spreadsheet Operations:** List all accessible spreadsheets.
- **Worksheet Operations:** List worksheets within a spreadsheet and retrieve paginated worksheet data.
- **Cell Operations:** Get, update, and clear individual cells.
- **Row Operations:** Get, update, and delete entire rows.
- **Column Operations:** Get, update, and delete entire columns.
- **Configuration via Environment Variables:** Service account credentials are passed as a base64-encoded string.

## Prerequisites

- Python 3.7 or higher
- [pip](https://pip.pypa.io/en/stable/)
- A Google Service Account with access to your target spreadsheets.

## Setup

### 1. Prepare the Service Account Credentials

1. **Encode the Service Account JSON file as base64:**

   ```bash
   base64 xxxxxxxx-2e4c92dc90c7.json > service_account_b64.txt
   ```

2. **Set the Environment Variable:**

   Copy the content from `service_account_b64.txt` and set it as the value for `SERVICE_ACCOUNT_B64`.

   For example, on Linux or macOS, you can set it like this:

   ```bash
   export SERVICE_ACCOUNT_B64="PASTE_YOUR_BASE64_STRING_HERE"
   ```

   If you're using Docker, you can pass this environment variable when running the container.

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install fastapi uvicorn gspread google-auth google-auth-oauthlib google-auth-httplib2
```

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

You can now access the Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to view and test the API endpoints.

## API Endpoints

The service exposes several endpoints. Here’s a brief overview:

### Spreadsheet Operations
- **List All Spreadsheets:**  
  `GET /spreadsheets`  
  Returns a list of spreadsheets accessible by the service account.

### Worksheet Operations
- **List Worksheets in a Spreadsheet:**  
  `GET /spreadsheets/{spreadsheet_id}/worksheets`  
  Retrieves all worksheets (tabs) in the specified spreadsheet.
  
- **Get Worksheet Data (Paginated):**  
  `GET /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}`  
  Accepts query parameters `start_row` and `end_row` to paginate the data.

### Cell Operations
- **Get a Single Cell Value:**  
  `GET /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}`

- **Update a Single Cell:**  
  `PATCH /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}`  
  Request Body Example:
  ```json
  {
    "value": "New Value"
  }
  ```

- **Delete (Clear) a Single Cell:**  
  `DELETE /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}`

### Row Operations
- **Get an Entire Row:**  
  `GET /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}`

- **Update an Entire Row:**  
  `PATCH /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}`  
  Request Body Example:
  ```json
  {
    "values": ["New Value 1", "New Value 2", "New Value 3"]
  }
  ```

- **Delete an Entire Row:**  
  `DELETE /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}`

### Column Operations
- **Get an Entire Column:**  
  `GET /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}`

- **Update an Entire Column:**  
  `PATCH /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}`  
  Request Body Example:
  ```json
  {
    "values": ["New Value 1", "New Value 2", "New Value 3"]
  }
  ```

- **Delete an Entire Column:**  
  `DELETE /spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}`

For more details, refer to the Swagger documentation available at `/docs` once the server is running.

## Docker

To run the service in a Docker container, create a `Dockerfile` similar to the following:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set the SERVICE_ACCOUNT_B64 environment variable (or pass it during container run)
ENV SERVICE_ACCOUNT_B64=<your_base64_string_here>

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run your Docker container:

```bash
docker build -t google-sheets-api .
docker run -p 8000:8000 -e SERVICE_ACCOUNT_B64="your_base64_string_here" google-sheets-api
```

## License

[Your License Information]

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Contact

For any questions or feedback, please reach out at [Your Contact Information or GitHub Repository Link].
