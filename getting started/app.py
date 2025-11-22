import streamlit as st
import asyncio
from fastmcp import Client

# Helper function to get the operator symbol
def get_operator(operation):
    operators = {
        "add": "+",
        "subtract": "-",
        "multiply": "×",
        "divide": "÷"
    }
    return operators.get(operation, "")

# Set up the page configuration
st.set_page_config(
    page_title="FastMCP Calculator",
    page_icon="🧮",
    layout="centered"
)

# Title and description
st.title("🧮 FastMCP Calculator")
st.markdown("Perform arithmetic operations using FastMCP server.")

# Create a session state to store the result
if 'result' not in st.session_state:
    st.session_state.result = None

# Function to call the FastMCP server
async def perform_operation(operation, **kwargs):
    try:
        client = Client("http://localhost:8000/mcp")
        async with client:
            result = await client.call_tool(operation, kwargs)
            return result.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

# UI for operation selection
operation = st.selectbox(
    "Select operation:",
    ["add", "subtract", "multiply", "divide", "power"]
)

# Input fields based on operation
col1, col2 = st.columns(2)

if operation in ["add", "subtract", "multiply", "divide"]:
    with col1:
        a = st.number_input("Enter first number:", value=5.0)
    with col2:
        b = st.number_input("Enter second number:", value=3.0)
elif operation == "power":
    with col1:
        base = st.number_input("Enter base:", value=2.0)
    with col2:
        exponent = st.number_input("Enter exponent:", value=3.0)

# Button to perform calculation
if st.button("Calculate"):
    if operation in ["add", "subtract", "multiply", "divide"]:
        # Handle division by zero
        if operation == "divide" and b == 0:
            st.error("Cannot divide by zero!")
        else:
            with st.spinner("Calculating..."):
                result = asyncio.run(perform_operation(operation, a=a, b=b))
                st.session_state.result = f"{a} {get_operator(operation)} {b} = {result}"
    elif operation == "power":
        with st.spinner("Calculating..."):
            result = asyncio.run(perform_operation(operation, base=base, exponent=exponent))
            st.session_state.result = f"{base}^{exponent} = {result}"

# Display the result
if st.session_state.result:
    st.success(st.session_state.result)

# Information section
with st.expander("About this app"):
    st.markdown("""
    This Streamlit app connects to a FastMCP server that provides arithmetic operations.
    
    **Features:**
    - Addition
    - Subtraction
    - Multiplication
    - Division (with error handling for division by zero)
    - Power (exponentiation)
    
    **Requirements:**
    - FastMCP server running on http://localhost:8000/mcp
    - Streamlit installed (`pip install streamlit`)
    
    **To run this app:**
    ```
    streamlit run app_name.py
    ```
    """)