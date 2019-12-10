import requests
from fake_useragent import UserAgent
ua = UserAgent()
from bs4 import BeautifulSoup
import json
import plotly
import plotly.express as px
import sqlite3

CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}

def get_unique_key(url):
  return url

def make_request_using_cache(url, header):
    unique_ident = get_unique_key(url)

    if unique_ident in CACHE_DICTION:
        print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    else:
        print("Making a request for new data...")
        resp = requests.get(url, headers=header)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

baseurl = 'https://www.collegedata.com'
header = {'User-Agent': ua.chrome}
DBNAME = 'schools.db'

def get_result_for_school():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    def create_school_table(name_text, location, difficulty, a_rate, undergrad, grad, cost, website):
        insertion = (None, name_text, location, difficulty, a_rate, undergrad, grad, cost, website)
        statement = 'INSERT INTO "SCHOOL" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
    def create_location_table(location, population, city, state):
        insertion2= (None, location, population, city, state)
        statement2 = 'INSERT INTO "LOCATION" '
        statement2 += 'VALUES(?, ?, ?, ?, ?)'
        cur.execute(statement2, insertion2)
    directory_url = baseurl + '/en/explore-colleges/college-search/SearchByPreference/?SearchByPreference.Regions=Region+Great+Lakes&SearchByPreference.Regions=Region+Plains'
    page_text = make_request_using_cache(directory_url, header)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    info = page_soup.find("table", id='colleges_table_vitals')
    all_links = info.find_all("div", class_="t-title__details")
    schools = []
    location_dict = {}
    id = 1
    for link in all_links:
        links = link.find('a')['href']
        details_url = baseurl + links
        college_page = make_request_using_cache(details_url, header)
        college_soup = BeautifulSoup(college_page, 'html.parser')
        name = college_soup.find("h1", id='mainContent')
        name_text = name.text.strip()
        location = name.find_next_sibling('p').text.strip()
        city = location.split(",")[0].strip()
        state = location.split(",")[1].strip()
        admission_info = college_soup.find('dl', class_='dl-split-sm')
        difficulty = admission_info.find_all('dd')[0].text
        a_rate = admission_info.find_all('dd')[1].text
        undergrad = college_soup.find('span', class_ = 'h2').text
        grad_info = college_soup.find(class_='media-body')
        grad = grad_info.find('span', class_='h2').text
        money_info = college_soup.find_all('div', class_='card-body')[1]
        cost = money_info.find_all("dd")[1].get_text(separator=" ").strip()
        website_parent = college_soup.find('div', id='profile-overview')
        website = website_parent.find('a')['href']
        table4 = college_soup.find_all('dl', class_='dl-split-sm')[4]
        population = table4.find_all('dd')[0].text
        a_school = School(name_text, location, difficulty, a_rate, grad, undergrad, cost, population)
        schools.append(a_school)
        if location not in location_dict:
            location_dict[location] = id
            create_location_table(location, population, city, state)
            id += 1
        create_school_table(name_text, location_dict[location], difficulty, a_rate, undergrad, grad, cost, website)
    conn.commit()
    conn.close()
    return schools

def init_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        DROP TABLE IF EXISTS 'School';
        '''
    cur.execute(statement)
    statement= '''CREATE TABLE "School" (
	"ID "	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT,
	"LocationID"	INTEGER,
	"Difficulty"	TEXT,
	"Acceptance Rate"	TEXT,
	"Undergraduate Size" TEXT,
    "Graduate Size" TEXT,
	"Cost"	TEXT,
	"Website"	TEXT,
	FOREIGN KEY("LocationID") REFERENCES "Location"("ID")
    );'''
    cur.execute(statement)
    conn.commit()
    statement = '''
        DROP TABLE IF EXISTS 'Location';
        '''
    cur.execute(statement)
    statement = '''CREATE TABLE "Location" (
	"ID"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Location"	TEXT,
	"Population"	INTEGER,
    "City" TEXT,
    "State" TEXT
    );'''
    cur.execute(statement)
    conn.commit()
    conn.close()

class School():
    def __init__(self, name, location = None, difficulty = None, a_rate = None, grad_size = None, undergrad_size = None, size = None, cost = None, population = None):
        self.name = name
        self.location = location
        self.difficulty = difficulty
        self.a_rate = a_rate
        self.grad_size = grad_size
        self.undergrad_size = undergrad_size
        self.size = size
        self.cost = cost
        self.population = population

    def __str__(self):
        return "{} ({}), Difficulty: {}, Admission Rate: {}, Undergraduate Size: {}, Graduate Size: {}, Cost: {}".format(self.name, self.location, self.difficulty, self.a_rate, self.grad_size, self.undergrad_size, self.cost, self.population)

def process_command(command, state_input):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    def pop_size(state_abbr):
        sql = "SELECT Name, [Graduate Size], [Undergraduate Size], Location.Population FROM School JOIN Location ON LocationID = Location.ID WHERE Location.State = '" + state_abbr + "'"
        data = cur.execute(sql)
        size_list = []
        pop_list = []
        name_list = []
        for info in data:
            graduate_size = info[1].replace(",", "")
            undergraduate_size = info[2].replace(",", "")

            if type(info[3]) == int:
                pass
            else:
                population = info[3].replace(",", "").strip()
            school = School(info[0], grad_size = graduate_size, undergrad_size = undergraduate_size, population = population)

            if school.undergrad_size == "Not reported" and school.grad_size == "Not reported":
                school.size = "Not reported"
            elif school.undergrad_size == "Not reported":
                school.size = int(school.grad_size)
            elif school.grad_size == "Not reported":
                school.size = int(school.undergrad_size)
            else:
                school.size = int(school.undergrad_size) + int(school.grad_size)

            if school.size == "Not reported" or school.population == "":
                pass
            elif int(school.population) >= 3000000:
                pass
            else:
                name_list.append(school.name)
                size_list.append(school.size)
                pop_list.append(int(school.population))
        return name_list, size_list, pop_list

    def pop_size_graph(state_abbr):
        all_lists = pop_size(state_abbr)
        name_list = all_lists[0]
        size_list = all_lists[1]
        pop_list = all_lists[2]
        fig = px.scatter(x=size_list, y=pop_list, hover_name=name_list)
        fig.update_layout(title="City Population and Student Body Size", xaxis_title="Student Body Size (Undergraduates and Graduates)", yaxis_title="City Population")
        fig.show()

    def difficulty(state_abbr):
        sql = "SELECT Difficulty FROM School JOIN Location ON Location.ID = LocationID WHERE Location.State = '" + state_abbr + "'"
        data = cur.execute(sql)
        difficult_dict = {}
        not_reported = 0
        noncompetitive = 0
        minimal_difficult = 0
        moderate_difficult = 0
        very_difficult = 0
        for info in data:
            if info[0] == 'Not reported':
                not_reported +=1
            elif info[0] == 'Noncompetitive':
                noncompetitive +=1
            elif info[0] == 'Minimally difficult':
                minimal_difficult += 1
            elif info[0] == 'Moderately difficult':
                moderate_difficult += 1
            elif info[0] == 'Very difficult':
                very_difficult += 1
        difficult_dict["Not reported"] = not_reported
        difficult_dict["Noncompetitive"] = noncompetitive
        difficult_dict["Minimally difficult"] = minimal_difficult
        difficult_dict["Moderately difficult"] = moderate_difficult
        difficult_dict["Very difficult"] = very_difficult
        return difficult_dict

    def difficult_bar_graph(state_abbr):
        difficult_dict = difficulty(state_abbr)
        fig = px.bar(x=list(difficult_dict.keys()), y=list(difficult_dict.values()))
        fig.update_layout(title="Schools' Entrance Difficulty", xaxis_title="Difficulty", yaxis_title="Count of Schools")
        fig.show()

    def search_schools_by_state(state_abbr):
        schools = cur.execute("SELECT NAME FROM School JOIN Location ON LocationID = Location.ID WHERE Location.State = '"+ state_abbr + "'")
        school_dict = {}
        i = 1
        for school in schools:
            school_dict[i] = (school[0])
            i+=1
        return school_dict

    def undergrad_grad(school):
        sql = "SELECT Name, [Graduate Size], [Undergraduate Size] FROM School WHERE Name ='" + school + "'"
        data = cur.execute(sql)
        for info in data:
            if info[1] == "Not reported":
                graduate_size = 0
            else:
                graduate_size = info[1].replace(",", "")
            if info[2] == "Not reported":
                undergraduate_size = 0
            else:
                undergraduate_size = info[2].replace(",", "")
            school = School(info[0], undergrad_size = int(undergraduate_size), grad_size = int(graduate_size))
        return school.name, school.undergrad_size, school.grad_size

    def undergrad_grad_graph(school):
        all_info = undergrad_grad(school)
        name = all_info[0]
        undergrad_size = all_info[1]
        grad_size = all_info[2]
        fig = px.bar(x=["Undergraduate", "Graduate"], y=[undergrad_size, grad_size])
        fig.update_layout(title="Undergraduate vs Graduate Students in " + school, xaxis_title="Student Body", yaxis_title="Count of Students")
        fig.show()

    def cost_acceptance(state_abbr):
        data = cur.execute("SELECT Name, Cost, [Acceptance Rate] FROM School JOIN Location ON LocationID = Location.Id WHERE Location.state = '" + state_abbr + "'")
        name_list = []
        final_attend_cost = []
        final_accept_rate = []
        for info in data:
            school = School(info[0], cost = info[1], a_rate = info[2])
            if school.cost == "Not reported" or school.a_rate == "Not reported":
                pass
            elif "In-state" in school.cost or "Out-of-state" in school.cost:
                name_list.append(school.name)
                in_state_cost = school.cost.split(" ")[1].replace("$", "").replace(",","")
                out_state_cost = school.cost.split(" ")[3].replace("$", "").replace(",","")
                attend_cost = (int(in_state_cost) + int(out_state_cost))/2
                final_attend_cost.append(attend_cost)
                accept_rate = int(school.a_rate.split("%")[0])/100
                final_accept_rate.append(accept_rate)
            else:
                name_list.append(school.name)
                attend_cost = school.cost.replace("$", "").replace(",","")
                final_attend_cost.append(attend_cost)
                accept_rate = int(school.a_rate.split("%")[0])/100
                final_accept_rate.append(accept_rate)
        return name_list, final_attend_cost, final_accept_rate

    def cost_acceptance_graph(state_abbr):
        all_lists = cost_acceptance(state_abbr)
        name = all_lists[0]
        cost = all_lists[1]
        acceptance = all_lists[2]
        fig = px.scatter(x=acceptance, y=cost, hover_name=name)
        fig.update_layout(title="Cost vs Acceptance Rate", xaxis_title="Acceptance Rate", yaxis_title="Cost")
        fig.show()

    if command == "1":
        pop_size_graph(state_input)
    elif command == "2":
        difficult_bar_graph(state_input)
    elif command == "3":
        school_dictionary = search_schools_by_state(state_input)
        for key, value in school_dictionary.items():
            print(f'{key:5} {value:5}')
        get_school = int(input("Please select a school by the number: "))
        while get_school > len(school_dictionary):
            get_school = int(input("Please select a school by the number: "))
        if get_school <= len(school_dictionary):
            undergrad_grad_graph(school_dictionary[get_school])
    elif command == "4":
        cost_acceptance_graph(state_input)

    conn.commit()
    conn.close()

def show_help_text():
    return ("""
    Choose a type of graph from the list.

    1 City Population and Student Body Size
    2 Schools' Entrance Difficulty
    3 Undergraduate vs Graduate Size at a School
    4 Cost vs Acceptance Rate

    Then search a Midwestern state to get data.

    If List Option 3: Pick a school from the list to compare undergraduate and graduate size.
    """)

def interactive_prompt():
    help_text = show_help_text()
    response = ''
    print ('''
    1 City Population and Student Body Size
    2 Schools' Entrance Difficulty
    3 Undergraduate vs Graduate Size at a School
    4 Cost vs Acceptance Rate
    ''')

    midwest_state_abbr = ["ND", "SD", "NE", "KS", "MN", "IA", "MO", "WI", "IL", "MI", "IN", "OH"]
    midwest_state_dict = {
    'ILLINOIS': 'IL',
    'INDIANA': 'IN',
    'IOWA': 'IA',
    'KANSAS': 'KS',
    'MICHIGAN': 'MI',
    'MINNESOTA': 'MN',
    'MISSOURI': 'MO',
    'NEBRASKA': 'NE',
    'NORTH DAKOTA': 'ND',
    'OHIO': 'OH',
    'SOUTH DAKOTA': 'SD',
    'WISCONSIN': 'WI',
    }

    while response != 'exit':
        response = input('Please select a visual: ')
        graph_options = ["1", "2", "3", "4"]
        if response == 'help':
            print(help_text)
            continue
        elif response == 'exit':
            pass
        elif response == "":
            continue
        elif response in graph_options:
            get_state = input("Please enter a Midwestern state: ").upper()
            abbrev_us_state = dict(map(reversed, midwest_state_dict.items()))
            while get_state not in list(midwest_state_dict.values()) and get_state not in list(midwest_state_dict.keys()):
                get_state = input("Please enter a Midwestern state: ").upper()
            if get_state in list(midwest_state_dict.keys()):
                get_state_abbr = midwest_state_dict[get_state]
            elif type(get_state) == "int":
                pass
            else:
                get_state_abbr = get_state
            process_command(response, get_state_abbr)
        else:
            print("Command not recognized: " + response)
    print('bye')


if __name__ == "__main__":
    init_db()
    get_result_for_school()
    interactive_prompt()
