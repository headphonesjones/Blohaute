from django.test import TestCase

class EmployeeSelectionTest(TestCase):

    def employee_list_returns_list_of_employees(self):
        response = self.client.get('/api/availability/stylists/')
