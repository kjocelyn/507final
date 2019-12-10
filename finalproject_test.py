from finalproject import *
from bs4 import BeautifulSoup
import unittest
from unittest import mock
import sys

DBNAME = 'schools.db'

class TestDataAccess(unittest.TestCase):
    def test_website_exists(self):
        request = requests.get('https://www.collegedata.com')
        self.assertEqual(request.status_code, 200)

    def test_data_access(self):
        school = get_result_for_school()
        self.assertEqual(school[0].name, "University of Michigan - Flint" )
        self.assertEqual(school[1].name, "University of Detroit Mercy")
        self.assertEqual(school[2].name, "Cleary University")

    def test_database(self):
        conn = sqlite3.connect(DBNAME)
        self.assertIsNotNone(conn)
        conn.close()

    def test_school_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        cur.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='School'
        ''')
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

    def test_location_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        cur.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Location'
        ''')
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()


class TestQueries(unittest.TestCase):
    def test_pop_size_query(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
            SELECT Name, [Graduate Size], [Undergraduate Size], Location.Population
            FROM School JOIN Location ON LocationID = Location.ID
            WHERE Location.State = 'MI'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('University of Michigan', '16,398', '30,318', '117,025'), result_list)
        conn.close()

    def test_difficulty_query(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
        SELECT Difficulty
        FROM School JOIN Location ON Location.ID = LocationID
        WHERE Location.State = 'MI'
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()[0]
        self.assertIn(('Moderately difficult'), result_list)
        conn.close()

    def test_search_school(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
        SELECT Name
        FROM School JOIN Location ON LocationID = Location.ID
        WHERE Location.State = 'MI'
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()[0]
        self.assertIn(('University of Michigan - Flint'), result_list)
        conn.close()

    def test_undergrad_grad(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
        SELECT Name, [Graduate Size], [Undergraduate Size] FROM School WHERE Name = 'University of Michigan - Dearborn'
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()
        self.assertEqual(result_list, ('University of Michigan - Dearborn', '3,254', '7,185'))
        conn.close()

    def test_cost_acceptance_query(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
        SELECT Name, Cost, [Acceptance Rate]
        FROM School JOIN Location ON LocationID = Location.Id
        WHERE Location.state = 'MI'
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()
        self.assertEqual(result_list, ('University of Michigan - Flint', 'In-state: $11,820 Out-of-state: $22,578', '65% of 4,558 applicants were admitted'))
        conn.close()

    def test_average_cost(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        sql = '''
        SELECT Name, Cost, [Acceptance Rate]
        FROM School JOIN Location ON LocationID = Location.Id
        WHERE Location.state = 'MI'
        '''
        results = cur.execute(sql)
        result_list = results.fetchone()[1]
        if "In-state" in result_list or "Out-of-state" in result_list:
            in_state_cost = result_list.split(" ")[1].replace("$", "").replace(",","")
            out_state_cost = result_list.split(" ")[3].replace("$", "").replace(",","")
            attend_cost = (int(in_state_cost) + int(out_state_cost))/2
        self.assertEqual(attend_cost, 17199)
        conn.close()

class TestGraphing(unittest.TestCase):
    def setUp(self):
        import sqlite3
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_pop_size_graph(self):
        try:
            process_command("1", "MI")
        except:
            self.fail()

    def test_difficulty_graph(self):
        try:
            process_command("2", "IN")
        except:
            self.fail()

    def test_undergrad_grad_graph(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
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

        try:
            undergrad_grad_graph("University of Michigan")
        except:
            self.fail()

        conn.close()

    def test_cost_acceptance_graph(self):
        try:
            process_command("4", "OH")
        except:
            self.fail()

if __name__ == '__main__':
    unittest.main()
