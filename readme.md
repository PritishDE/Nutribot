# Nutrition Data Chatbot

A Streamlit-based chatbot that allows users to query nutrition data using natural language, powered by Snowflake Cortex Analyst & Cortex Complete.

## Features

- Natural language processing of nutrition-related queries
- Direct integration with Snowflake data warehouse
- Real-time responses based on actual data
- Chat history preservation
- Leverages a semantic model for intuitive, business-friendly data access

## Prerequisites

- Python 3.8 or higher
- Snowflake account with Cortex Analyst enabled
- Access to a nutrition data table in Snowflake

## Setup

1. Clone this repository
2. Upload the semantic model, and nutrition data into Snowflake stage
3. Create a Streamlit app in Snowflake via Snowsight & Paste the contents of your ttyd.py

## Usage

- The local code is in progress, for now the codebase can be executed in only SIS (Streamlit in Snowflake)

## Example Queries

- "Which food has the highest protein content?"
- "Show me low-carb recipes"
- "What are the top 5 foods with the highest fat content?"
- "List vegetarian recipes with more than 20g of protein"


## Performance Optimization

- The app uses Snowflake Cortex Analyst for efficient query processing
- Results are cached in the session state
