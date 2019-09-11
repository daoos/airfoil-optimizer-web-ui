import json
import unittest

from project import db
from project.api.models import Run
from project.tests.base import BaseTestCase


def add_run(*args, **kwargs):
    run = Run(*args, **kwargs)
    db.session.add(run)
    db.session.commit()
    return run


class TestRunsService(BaseTestCase):
    """Tests for the Runs Service."""

    def test_runs(self):
        """Ensure the /ping route behaves correctly."""
        response = self.client.get('/runs/ping')
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIn('pong!', data['message'])
        self.assertIn('success', data['status'])

    def test_add_run(self):
        """Ensure a new run can be added to the database."""
        with self.client:
            response = self.client.post(
                '/runs',
                data=json.dumps({
                    'cl': 1.0, 'n_c': 3, 'n_t': 3, 'b_c': 8, 'b_t': 8,
                    'gen': 100, 'constrain_moment': False, 'report': False
                }),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 201)
            self.assertIn('New run was added!', data['message'])
            self.assertIn('success', data['status'])

    def test_add_run_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        with self.client:
            response = self.client.post(
                '/runs',
                data=json.dumps({}),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid payload.', data['message'])
            self.assertIn('fail', data['status'])

    def test_add_run_invalid_json_keys(self):
        """
        Ensure error is thrown is the JSON object does not have all required keys.
        """
        with self.client:
            response = self.client.post(
                '/runs',
                data=json.dumps({'cl': 1.0}),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid payload.', data['message'])
            self.assertIn('fail', data['status'])

    def test_single_run(self):
        """Ensure get single run behaves correctly."""
        run = add_run(cl=1.0, n_c=3, n_t=3)
        with self.client:
            response = self.client.get(f'/runs/{run.id}')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(1.0, data['data']['cl'])
            self.assertEqual(3, data['data']['n_c'])
            self.assertEqual(3, data['data']['n_t'])
            self.assertIn('success', data['status'])

    def test_single_user_no_id(self):
        """Ensure error is thrown is an id is not provided."""
        with self.client:
            response = self.client.get(f'/runs/blah')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 404)
            self.assertIn('Run does not exist', data['message'])
            self.assertIn('fail', data['status'])

    def test_single_user_incorrect_id(self):
        """Ensure error is thrown if the id does not exist."""
        with self.client:
            response = self.client.get(f'/runs/999')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 404)
            self.assertIn('Run does not exist', data['message'])
            self.assertIn('fail', data['status'])

    def test_all_runs(self):
        """Ensure get all runs behaves correctly."""
        add_run(1.0, 3, 3)
        add_run(0.5, 6, 6, 16, 16)
        with self.client:
            response = self.client.get('/runs')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data['data']['runs']), 2)

            self.assertEqual(1.0, data['data']['runs'][0]['cl'])
            self.assertEqual(3, data['data']['runs'][0]['n_c'])
            self.assertEqual(3, data['data']['runs'][0]['n_t'])

            self.assertEqual(0.5, data['data']['runs'][1]['cl'])
            self.assertEqual(6, data['data']['runs'][1]['n_c'])
            self.assertEqual(6, data['data']['runs'][1]['n_t'])
            self.assertEqual(16, data['data']['runs'][1]['b_c'])
            self.assertEqual(16, data['data']['runs'][1]['b_t'])

            self.assertIn('success', data['status'])





if __name__ == '__main__':
    unittest.main()
