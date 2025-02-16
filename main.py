from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import base64

app = FastAPI(
    title="Google Sheets API",
    description=(
        "A FastAPI service to interact with Google Sheets via gspread.\n\n"
        "### Overview\n"
        "- **Spreadsheet Operations:** List all accessible spreadsheets.\n"
        "- **Worksheet Operations:** List worksheets, get paginated data, and perform cell, row, or column updates/deletions.\n"
        "- **Examples:** See the request body examples for PATCH endpoints below."
    ),
    version="0.1.0",
)

# -------------------------------------------------------------------
# 1) AUTHENTICATION / CLIENT INIT
# -------------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"  # Needed to list spreadsheets in Drive
]

# Load the base64-encoded service account JSON from an environment variable
service_account_b64 = os.environ.get("SERVICE_ACCOUNT_B64")
if not service_account_b64:
    raise Exception("Environment variable SERVICE_ACCOUNT_B64 not found.")

# Decode the base64 string and load the JSON into a dict
service_account_info = json.loads(base64.b64decode(service_account_b64))

# Create credentials from the service account info
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

gc = gspread.authorize(creds)

# -------------------------------------------------------------------
# 2) Pydantic MODELS WITH EXAMPLES
# -------------------------------------------------------------------
class UpdateCellModel(BaseModel):
    value: str = Field(..., example="Hello, World!")

class UpdateRowModel(BaseModel):
    values: List[str] = Field(..., example=["Row value 1", "Row value 2", "Row value 3"])

class UpdateColumnModel(BaseModel):
    values: List[str] = Field(..., example=["Column value 1", "Column value 2", "Column value 3"])

# -------------------------------------------------------------------
# 3) HELPER FUNCTIONS
# -------------------------------------------------------------------
def column_letter_to_index(letter: str) -> int:
    """
    Convert a column letter (e.g., 'B', 'AA') to a 1-indexed column number.
    """
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result

def column_index_to_letter(index: int) -> str:
    """
    Convert a 1-indexed column number to its corresponding Excel column letter.
    """
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result

# -------------------------------------------------------------------
# 4) ENDPOINTS
# -------------------------------------------------------------------

# ------------------ 4.1: List All Spreadsheets --------------------
@app.get("/spreadsheets", tags=["Spreadsheets"])
def list_spreadsheets():
    """
    **List Spreadsheets**

    Retrieve a list of spreadsheets accessible by the service account.
    """
    try:
        spreadsheets = gc.openall()
        result = [{"title": sh.title, "id": sh.id} for sh in spreadsheets]
        return {"spreadsheets": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.2: List Worksheets in a Spreadsheet --------------------
@app.get("/spreadsheets/{spreadsheet_id}/worksheets", tags=["Worksheets"])
def list_worksheets(spreadsheet_id: str):
    """
    **List Worksheets**

    Retrieve all worksheets (tabs) in a specified spreadsheet.

    **Example Response:**
    ```json
    {
      "worksheets": [
        {"title": "Sheet1", "id": 0, "rows": 100, "cols": 26},
        {"title": "Sheet2", "id": 123456, "rows": 50, "cols": 10}
      ]
    }
    ```
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheets_info = []
        for ws in sh.worksheets():
            worksheets_info.append({
                "title": ws.title,
                "id": ws.id,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        return {"worksheets": worksheets_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.3: Get Worksheet Data (Paginated by Row) --------------------
@app.get("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}", tags=["Worksheets"])
def get_worksheet_data(
    spreadsheet_id: str,
    worksheet_title: str,
    start_row: int = Query(1, description="Starting row for pagination (default is 1)"),
    end_row: int = Query(10, description="Ending row for pagination (default is 10)")
):
    """
    **Get Worksheet Data**

    Retrieve data from a specific worksheet using pagination by row range.
    
    **Example:**  
    GET `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1?start_row=1&end_row=10`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        data_range = f"A{start_row}:Z{end_row}"  # Adjust if more columns are needed.
        data = ws.get(data_range)
        return {
            "worksheet": worksheet_title,
            "range": data_range,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.4: Update a Single Cell --------------------
@app.patch("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}", tags=["Worksheets"])
def update_single_cell(
    spreadsheet_id: str,
    worksheet_title: str,
    cell_address: str,
    body: UpdateCellModel
):
    """
    **Update Single Cell**

    Update a single cell in the worksheet.

    **Example Request Body:**
    ```json
    {
      "value": "Hello, World!"
    }
    ```
    
    **Example Endpoint:**  
    PATCH `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1/cell/B14`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        ws.update_acell(cell_address, body.value)
        return {"message": f"Cell {cell_address} updated with value '{body.value}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.5: Get a Single Cell Value --------------------
@app.get("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}", tags=["Worksheets"])
def get_single_cell(
    spreadsheet_id: str,
    worksheet_title: str,
    cell_address: str
):
    """
    **Get Single Cell**

    Retrieve the value of a single cell (e.g., 'B14') in a worksheet.
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        value = ws.acell(cell_address).value
        return {"cell": cell_address, "value": value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.6: Get an Entire Row --------------------
@app.get("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}", tags=["Worksheets"])
def get_row(
    spreadsheet_id: str,
    worksheet_title: str,
    row_number: int
):
    """
    **Get Row**

    Retrieve all values from a specific row in a worksheet.

    **Example:**  
    GET `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1/row/5`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        row_values = ws.row_values(row_number)
        return {"row": row_number, "values": row_values}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.7: Get an Entire Column --------------------
@app.get("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}", tags=["Worksheets"])
def get_column(
    spreadsheet_id: str,
    worksheet_title: str,
    column_letter: str
):
    """
    **Get Column**

    Retrieve all values from a specific column in a worksheet.

    **Example:**  
    GET `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1/column/B`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        col_index = column_letter_to_index(column_letter)
        col_values = ws.col_values(col_index)
        return {"column": column_letter.upper(), "values": col_values}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.8: Delete (Clear) a Single Cell --------------------
@app.delete("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/cell/{cell_address}", tags=["Worksheets"])
def delete_cell(
    spreadsheet_id: str,
    worksheet_title: str,
    cell_address: str
):
    """
    **Delete (Clear) a Cell**

    Clear the content of a single cell (e.g., 'B14').  
    _Note: This operation clears the cell content rather than deleting its structure._
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        ws.update_acell(cell_address, "")
        return {"message": f"Cell {cell_address} cleared."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.9: Delete an Entire Row --------------------
@app.delete("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}", tags=["Worksheets"])
def delete_row(
    spreadsheet_id: str,
    worksheet_title: str,
    row_number: int
):
    """
    **Delete Row**

    Delete an entire row from a worksheet.
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        ws.delete_rows(row_number)
        return {"message": f"Row {row_number} deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.10: Delete an Entire Column --------------------
@app.delete("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}", tags=["Worksheets"])
def delete_column(
    spreadsheet_id: str,
    worksheet_title: str,
    column_letter: str
):
    """
    **Delete Column**

    Delete an entire column from a worksheet.
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        col_index = column_letter_to_index(column_letter)
        ws.delete_column(col_index)
        return {"message": f"Column {column_letter.upper()} deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.11: Update an Entire Row --------------------
@app.patch("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/row/{row_number}", tags=["Worksheets"])
def update_row(
    spreadsheet_id: str,
    worksheet_title: str,
    row_number: int,
    body: UpdateRowModel
):
    """
    **Update Row**

    Update an entire row in a worksheet.  
    The provided list of values will update the row starting from column A.

    **Example Request Body:**
    ```json
    {
      "values": ["New Value 1", "New Value 2", "New Value 3"]
    }
    ```
    
    **Example Endpoint:**  
    PATCH `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1/row/5`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        num_values = len(body.values)
        if num_values == 0:
            raise HTTPException(status_code=400, detail="No values provided for the row update.")
        end_column_letter = column_index_to_letter(num_values)
        cell_range = f"A{row_number}:{end_column_letter}{row_number}"
        ws.update(cell_range, [body.values])
        return {"message": f"Row {row_number} updated.", "values": body.values}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ 4.12: Update an Entire Column --------------------
@app.patch("/spreadsheets/{spreadsheet_id}/worksheets/{worksheet_title}/column/{column_letter}", tags=["Worksheets"])
def update_column(
    spreadsheet_id: str,
    worksheet_title: str,
    column_letter: str,
    body: UpdateColumnModel
):
    """
    **Update Column**

    Update an entire column in a worksheet.  
    The provided list of values will update the column starting from row 1.

    **Example Request Body:**
    ```json
    {
      "values": ["New Value 1", "New Value 2", "New Value 3"]
    }
    ```
    
    **Example Endpoint:**  
    PATCH `/spreadsheets/{spreadsheet_id}/worksheets/Sheet1/column/B`
    """
    try:
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        num_values = len(body.values)
        if num_values == 0:
            raise HTTPException(status_code=400, detail="No values provided for the column update.")
        cell_range = f"{column_letter.upper()}1:{column_letter.upper()}{num_values}"
        column_values = [[val] for val in body.values]
        ws.update(cell_range, column_values)
        return {"message": f"Column {column_letter.upper()} updated.", "values": body.values}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
