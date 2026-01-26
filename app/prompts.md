# AI Prompts Configuration

## metadata_extraction
Extract metadata from user query to understand intent, chart type, and visualization requirements.

### USER QUERY:
{user_query}

---

## datasource_selection
Select the most appropriate datasource for a user query.

### AVAILABLE DATASOURCES:
{datasources_info}

### USER QUERY:
{user_query}

---

## metadata_update
Update the metadata based on the edit.

### ORIGINAL USER QUERY:
{original_user_query}

### EDIT HISTORY: 
{history_context}

### LAST EDIT INSTRUCTIONS:
{edit_instructions}

Generate updated title, description, chart_type, and config if needed.

---

## query_edit
Modify the existing visualization based on user instructions. Some fields may not need to be changed.

### ORIGINAL VISUALIZATION:
- Title: {title}
- Chart Type: {chart_type}
- Data Source: {data_source}
- Original User Query: {original_user_query}
- Last Database Query: {last_query}
- X Column: {x_column}
- Y Column: {y_column}

### NEW VISUALIZATION METADATA
- Chart Type: {new_chart_type}

### EDIT HISTORY:
{history_context}

### DATABASE SCHEMA:
{schema}

### USER EDIT INSTRUCTIONS:
{edit_instructions}

Generate the updated query maintaining the same output structure.
