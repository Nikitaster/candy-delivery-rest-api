couriers_create_test_json = {
    'requests': [
        {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": []
                }
            ]
        },
        {
            "data": [
                {
                    "courier_id": 4,
                    "courier_type": "test",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                }
            ]
        },
        {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 2222222],
                    "working_hours": ["11:35-14:05test", "09:00-11:00"]
                }
            ]
        },
    ],
    'responses': [
        {
            'status_code': 201,
            'json': {"couriers": [{"id": 1}, {"id": 2}, {"id": 3}]}
        },
        {
            'status_code': 400,
            'json': {
                "validation_error": {
                    "courier_type": [
                        "test"
                    ]
                }
            }
        },
        {
            'status_code': 400,
            'json': {
                "validation_error": {
                    "couriers": [
                        {
                            "id": 1
                        }
                    ]
                }
            }
        }
    ]
}


couriers_patch_test_json = {
    'requests': [
        {
            "regions": [11, 33, 2, 1],
            "courier_type": "car",
            "working_hours": [
                "09:00-18:01"
            ]
        },
        {
            "regions": [11, 33, 2, 1],
            "courier_type": "car",
            "working_hours": [
                "09:00-18:01test"
            ]
        },
        {
            "test": "test"
        }
    ],
    'responses': [
        {
            'status_code': 200,
            'json':
                {
                    "courier_id": 1,
                    "courier_type": "car",
                    "regions": [
                        11,
                        33,
                        2,
                        1
                    ],
                    "working_hours": [
                        "09:00-18:01"
                    ]
                }
        },
        {
            'status_code': 400,
            'json':
                {
                    "validation_error": [
                        {
                            "courier_id": 1,
                            "working_hours": "09:00-18:01test"
                        }
                    ]
                }
        },
        {
            'status_code': 400,
            'json':
                {
                    "errs": [
                        "test"
                    ]
                }
        }
    ]
}
