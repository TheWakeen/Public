import pandas as pd
import tkinter as tk
import os
import graphviz
from math import log2
from random import random
from tkinter import filedialog

window = tk.Tk()
window.withdraw()

def temperature_transform(temperature):
    if temperature > 85:
        return "Hot"
    elif temperature <= 85 or temperature >= 40:
        return "Mild"
    else: return "Cold"

def humidity_transform(humidity):
    if humidity > 70:
        return "High"
    else: return "Normal"

def wind_transform(wind):
    if wind > 7:
        return "High"
    elif wind > 0: return "Low"
    else: return "none"

def save_graph_as_jpg(graph, save_name):
    graph.save("temp.dot")
    src = graphviz.Source.from_file("temp.dot")
    src.render(save_name, format = "jpg")
    os.remove(save_name)
    os.remove("temp.dot")
    save_location = os.path.join(os.getcwd(), save_name)
    print("Saving", save_name, "to the following directory", save_location)

def save_cleaned_df(df, save_name):
    save_location = os.path.join(os.getcwd(), save_name + ".csv")
    df.to_csv(save_location)
    print("Saving", save_name, "to the following diretory as a CSV", save_location)

class Node:
    def __init__(self, data, left = None, right = None):
        self.left = left
        self.right = right
        self.data = data

def safe_log2(value):
    if value > 0:
        return log2(value)
    else:
        return 0

def calculate_entropy(yes_count, no_count, total_rows):
    return -(yes_count/total_rows) * safe_log2(yes_count/total_rows) - \
           (no_count/total_rows) * safe_log2(no_count/total_rows)

def calculate_category_gain(df, category_name):
    print(category_name)
    result = df.columns[-1]
    total_rows = df[result].count()
    yes_count = sum((df[result] == "y") | (df[result] == "Y"))
    no_count = sum((df[result] == "n") | (df[result] == "N"))
    entropy = calculate_entropy(yes_count, no_count, total_rows)

    values = df[category_name].unique()

    gain = entropy

    for value in values:
        vdf = df[df[category_name] == value]
        value_total = vdf[vdf.columns[0]].count()
        value_yes = sum((vdf[result] == "y") | (vdf[result] == "Y"))
        value_no = sum((vdf[result] == "n") | (vdf[result] == "N"))
        value_entropy = calculate_entropy(value_yes, value_no, value_total)
        value_gain = (value_total / total_rows) * value_entropy
        # print("{} Entropy: {}, Gain: {}".format(value, value_entropy, value_gain))
        gain -= value_gain

    # print("{} Gain: {}", category_name, gain)

    return gain

def lerp(a, b, alpha):
    c = [0, 0, 0]
    for i in range(0, len(a)-1):
        c[i] = int(alpha*b[i] + (1.0-alpha)*a[i])
    return tuple(c)


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

# def rgb_to_hex(rgb):
#     return ('{:X}{:X}{:X}').format(int(rgb[0]), rgb[1], rgb[2])


def add_frame_to_graph_id3(dataframe, graph, parent_name="", edge_name=""):
    node_name = ""
    color = "white"
    node_id = str(random())

    result = dataframe.columns[-1]
    total_rows = dataframe[result].count()
    yes_count = sum((dataframe[result] == "y") | (dataframe[result] == "Y"))
    no_count = sum((dataframe[result] == "n") | (dataframe[result] == "N"))

    break_on_category = ""

 #   print(f"""Processing data frame:
 #    {dataframe}
 #   
 #    Total rows: {total_rows}
 #    Yes count: {yes_count}
 #    No count: {no_count}
 #   
 #    """)

# Tweek the entropy percentage and/or number of rows
    if yes_count/total_rows > .99:
        node_name = f"Yes {int((yes_count/total_rows)*100)}%"
        node_id += node_name
        color = "green"
    elif no_count/total_rows > .99:
        node_name = f"No {int((no_count/total_rows)*100)}%"
        node_id += node_name
        color = "red"
    elif len(dataframe.columns[0:-1]) > 0 and total_rows > 3:
        largest_gain = -1
        for category in dataframe.columns[0:-1]:
            gain = calculate_category_gain(dataframe, category)
            if gain > largest_gain:
                largest_gain = gain
                node_name = category
                break_on_category = category

        # Break on category
        node_id += node_name
    else:
        node_name = "Yes: {}%, No: {}%".format(int(100*(yes_count/total_rows)), int(100*(no_count/total_rows)))
        node_id += "Yes-{}-percent-No-{}-percent".format(int(100*(yes_count/total_rows)), int(100*(no_count/total_rows)))
        alpha = yes_count/total_rows
        color = f"#{rgb_to_hex(lerp((255, 0, 0), (0, 255, 0), alpha))}"

    entries = dataframe[dataframe.columns[0]].count()
    graph.node(node_id, f'''<
        <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" BGCOLOR="{color}">
          <TR>
            <TD>{node_name}</TD>
          </TR>
          <TR>
            <TD>{entries} rows</TD>
          </TR>
        </TABLE>>''')

    if edge_name:
        graph.edge(parent_name, node_id, label=str(edge_name))

    if break_on_category:
        # print(f"Breaking on category: {break_on_category}")
        values = df[break_on_category].unique()
        for value in values:
            vdf = dataframe[dataframe[break_on_category] == value]
            rows = vdf[vdf.columns[-1]].count()
            if rows > 0:
                # print(f"Value: {value}")
                # print(vdf)
                vdf = vdf.drop(columns=[break_on_category])
                # print(f"Dropping column: ")
                # print(vdf)
                add_frame_to_graph_id3(vdf, graph, node_id, value)

file_path = os.path.join(os.getcwd(),"outdoors.csv")

if os.path.exists(file_path):
   print("Found the file. Reading...")
else:
    print("File not found. Please select the file.")

    file_selection = filedialog.askopenfilename()

    if file_selection:
        print("selected file located at", file_selection)
        file_path = file_selection
    else:
        print("No file selected. Exiting...")

if file_path:
    #Reading the input file
    
    df = pd.read_csv(file_path)
    df['Temperature'] = df.apply(lambda row: temperature_transform(row["Temperature"]), axis = 1)
    df["Humidity"] = df.apply(lambda row: humidity_transform(row["Humidity"]), axis = 1)
    df["Wind"] = df.apply(lambda row: wind_transform(row["Wind"]), axis = 1)
    print(df)

    # Create Nodes for all entries in dataframe
    nodeMap = {None:None}


#this is the section where I realized that my outdoors-corrected.csv file isn't
#formatted in the correct formatting like we see in assignment three. 

    #process your data frame from the bottom up 
    print("Creating Nodes for Tree")
    for index in reversed(df.index.values):
    #print("Creating Node for: ",index)
        nodeMap[index] = Node(df.loc[index]["Outlook"],nodeMap[df.loc[index]["Humidity"]],nodeMap[df.loc[index]["Wind"]])
    
    s = graphviz.Digraph('structs', filename='structs.gv',
                     node_attr={'shape': 'plaintext'})

    # Assemble the tree top-down
    for node in reversed(nodeMap.values()):
        if(node == None):
            break

        #print("Inserting node for: ",node.data)
        graph.node(node.data)
        if node.left:
            graph.edge(node.data, node.left.data)
        if node.right:
            graph.edge(node.data, node.right.data)
    
    add_frame_to_graph_id3(df, s)
                    

    
save_name = input("Enter a save name: ")
if save_name:
    save_graph_as_jpg(s, save_name)
    save_cleaned_df(df, save_name)
else:
    Print("No save name entered. Exiting...")
    

