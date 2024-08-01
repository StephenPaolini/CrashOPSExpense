import sqlite3
import pandas as pd
import plotly.graph_objects as go
import panel as pn
from datetime import datetime

try:
    connection = sqlite3.connect("C:\\cm\\verf\\flaskApp\\DB.db")
    cursor = connection.cursor()
    print('connected')
except:
    print("could not connect")


menu = pn.widgets.Select(name='Select Year', options=[
                         '2023', '2024'], value='2024')




######################## DEFAULT DATAFRAME MANIPULATIONS ###################################
df = pd.read_sql_query("SELECT * from CrashExpense", connection)
month_qry = "SELECT Date FROM CrashExpense"

month_frame = pd.read_sql_query(month_qry, connection)

month_frame['Date'] = pd.to_datetime(month_frame['Date'])
month_frame['month'] = month_frame['Date'].dt.month_name(locale='English')

month_frame['year'] = month_frame['Date'].dt.year
df.insert(1, 'year', month_frame['year'])


curr_year = 'year == ' + str(datetime.now().year)
prev_year = 'year == ' + str(datetime.now().year - 1)

ytd_qry = df.query(curr_year)


YTD = ytd_qry['Price'].sum()

prev_year = df.query(prev_year)

prev_YTD = prev_year['Price'].sum()
cat_sums = df.groupby('Category')['Price'].sum().reset_index()
largest_spender = cat_sums.sort_values(by='Price', ascending=False).iloc[0]


df.insert(1, "month", month_frame['month'])


items = month_frame['year'].dropna().unique().tolist()

######################## DEFAULT DATAFRAME MANIPULATIONS ###################################

def selected_year(clicked):
    print(clicked)


def histogram_plot(x, category):
    df2 = df.query('year == ' + x)
    if category == 'All':
        dff = df2
    else:
        dff = df2[df2.Category == category]
    fig = go.Figure(go.Histogram(
        x=dff['month'], y=dff['Price'], histfunc='sum'))
    fig.update_layout(title_text='Total Monthly Expenses',
                      autosize=True, template="plotly_dark")

    return fig


@pn.depends(menu)
def pie_plot(x):
    dff = df.query('year == ' + x)
    dff['Price'] = pd.to_numeric(dff['Price'])
    cat_sums = dff.groupby('Category')['Price'].sum().reset_index()
    fig = go.Figure(
        go.Pie(labels=cat_sums['Category'], values=cat_sums['Price'], hole=.38))
    fig.update_layout(
        title_text='YTD - Overall Expenses by category', autosize=True, template="plotly_dark")

    return fig


@pn.depends(menu)
def line_plot(x):
    dff = df.query('year == ' + x)
    stream = pn.pane.Perspective(dff, plugin='d3_y_area', columns=['Price'], theme='material-dark', group_by=['month'], split_by=['Category'], sizing_mode='stretch_width', height=500, margin=0)
    
    
    
    return stream


table_filters = {
    'Date': {'type': 'input', 'func': 'like'},
    'month': {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': False},
    'year': {'type': 'input', 'func': 'like'},
    'PQ': {'type': 'input', 'func': 'like'}

}


@pn.depends(menu)
def table(x):
    dff = df.query('year ==' + x)
    table = pn.widgets.Tabulator(
        # theme='semantic-ui'
        dff.iloc[:], pagination='local', layout='fit_columns', page_size=9, sizing_mode='stretch_width', header_filters=table_filters,
    )
    return table


@pn.depends(menu)
def filter(x):
    YTD_qr = df.query('year ==' + x)
    YTD_fr = YTD_qr['Price'].sum()
    YTD_card = pn.indicators.Number(name='YTD Spending', value=YTD_fr, format='${:,.2f}'.format(
        YTD_fr), font_size='34pt', title_size='20pt', default_color='white')
    return YTD_card


data = {'x': [int(datetime.now().year-1),
              int(datetime.now().year)], 'y': [prev_YTD, YTD]}
trend = pn.indicators.Trend(
    name='Previous Year Trend', data=data, width=250, height=150, plot_type='bar', plot_color='#eb1f10')

# largest_spender_card = pn.widgets.Number(name='Largest Spender', value=largest_spender['Category'])



########################### TEMPLATE SETTINGS##################################
template = pn.template.FastGridTemplate(
    title="CrashOPS Expense Tracker",
    accent='#181818',
    prevent_collision=True,
    busy_indicator=None,
    theme_toggle=True,
    theme='dark',
    row_height=200,
    collapsed_sidebar=True

)

########################### TEMPLATE SETTINGS##################################

options_list = df.Category.dropna().unique().tolist()
options_list.append("All")
Select = pn.widgets.Select(
    name='Select', options=options_list)

bind_histogram = pn.bind(histogram_plot, x=menu, category=Select)

bind_menu = pn.bind(selected_year, clicked=menu)


# ##################################### MODAL WIDGETS / CODE #####################################
modal_btn = pn.widgets.Button(name='Enter new Purchase Request')

style_title = {
    'color': 'white',
    'font-size': '32px'
}

style_border = {
    'border-color': '#FFFFFF',
    
}
title = pn.widgets.StaticText(value='New Purchase Request',styles=style_title)


enter_pq = pn.widgets.TextInput(name='PQ Number', placeholder='CC-PQ-#####',styles=style_border)

price_in = pn.widgets.FloatInput(name='Enter Price', styles=style_border)

options_list_sel = options_list
options_list_sel.remove("All")
sel_cat = pn.widgets.Select(name='Select Category',
                            options=options_list, styles=style_border)

sel_date = pn.widgets.DatePicker(name='Select Date', styles=style_border)


sel_vendor = pn.widgets.AutocompleteInput(name='Select Vendor', options=df['Name'].unique().tolist(), case_sensitive=False, placeholder='Vendor Name')

enter_des = pn.widgets.TextAreaInput(name='Enter description')

enter_purp = pn.widgets.TextAreaInput(name='Enter Purpose')

initals = pn.widgets.TextInput(name='Enter intials of requester',placeholder='enter initials here...')


submit_btn  = pn.widgets.Button(name='Submit')

def open(event):
    template.open_modal()

# Push each value to the database
def submit(event):
    insert_qry = 'INSERT INTO CrashExpense (Date,PQ,Price,Category,Name,Description,Purpose,User) VALUES (?,?,?,?,?,?,?,?) '

    cursor.execute(insert_qry, (sel_date.value, enter_pq.value,price_in.value, sel_cat.value, sel_vendor.value, enter_des.value, enter_purp.value, initals.value))
    
    connection.commit()

    template.close_modal()

submit_btn.on_click(submit)

modal_btn.on_click(open)

# ##################################### MODAL WIDGETS / CODE #####################################


# This is what plots the graph on the page
# [height,width]
###################################################################

template.main[0:1, :2] = pn.Column(filter)
template.main[0:1, 2:4] = trend

###################################################################
template.main[1:3, :8] = pn.Column(Select, bind_histogram)
template.main[1:3, 8:12] = pie_plot
###################################################################
template.main[3:5, :12] = table
###################################################################
template.main[5:8, :12] = line_plot


# SIDEBAR
template.sidebar[:] = ['Filter by Year', pn.Column(menu, bind_menu)]
template.sidebar.append(pn.layout.Divider())
template.sidebar.append(modal_btn)


# MODAL
template.modal.append(title)
template.modal.append(pn.Row(enter_pq, price_in, sel_cat, sel_date))
template.modal.append(pn.Row(sel_vendor,enter_des,enter_purp,initals))
template.modal.append(pn.Row(submit_btn))


template.servable()