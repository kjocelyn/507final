# 507 final project 

Data Source: www.collegedata.com 

More Info: After running the program, you will be shown an interactive command prompt, which gives you four different options to visualize data from the data source. Based on the visualization you pick, you will need to enter a state name or state abbreviation. For option 3, you would need to enter the number that corresponds with the school after entering the state name (two command line prompts). After that, you will see the visualization you chose, either bar graphs or scatterplots through plotly. 

Structure: Caching was set up first, database was created, then data source was scraped and crawled and information was stored into the tables. Data was processed from the database and then mapped. One important function is process_command that takes user input and gives them the visualization they want. Another major function is pop_size, which takes the information from the database and adds graduate student size and undergraduate student size. It takes the total number of students in a school and compares it to the city population. It incorporates a class called School by creating objects and stores the data within the function. Some major data structures used are lists of student sizes, city populations in a state, and names of schools. There is also a dictionary that has a corresponding number with the name of the school {1: School Name}. 

python finalproject.py

1 City Population and Student Body Size
2 Schools' Entrance Difficulty
3 Undergraduate vs Graduate Size at a School
4 Cost vs Acceptance Rate

Please select a visual: 1
Please enter a Midwestern state: MI
(opens up graph)

Please select a visual: 3
Please enter a Midwestern state: North Dakota
    1 Dickinson State University
    2 University of Mary
    3 Rasmussen College - Fargo
    4 Mayville State University
    5 University of North Dakota
    6 Minot State University
    7 Jamestown College
    8 North Dakota State University
    9 Trinity Bible College
   10 Valley City State University
Please select a school by the number: 1
(opens up graph)

Please select a visual: help

Choose a type of graph from the list.

1 City Population and Student Body Size
2 Schools' Entrance Difficulty
3 Undergraduate vs Graduate Size at a School
4 Cost vs Acceptance Rate

Then search a Midwestern state to get data.

If List Option 3: Pick a school from the list to compare undergraduate and graduate size.

Please select a visual: exit       
bye

*Note: Visuals 1,2,4 have the same process
