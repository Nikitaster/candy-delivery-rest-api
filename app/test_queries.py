"""JSON requests and responses for tests."""

from datetime import datetime

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
        },
        {
            "regions": [11, 33, 2, 1],
            "courier_type": "foot",
            "working_hours": [
                "13:00-14:00"
            ]
        },
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
        },
        {
            'status_code': 200,
            'json':
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [
                        11,
                        33,
                        2,
                        1
                    ],
                    "working_hours": [
                        "13:00-14:00"
                    ]
                }
        },
    ]
}


orders_create_test_json = {
    'requests': [
        {
            "data": [
                {
                    "order_id": 444,
                    "weight": 0.23,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 555,
                    "weight": 15,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 666,
                    "weight": 0.01,
                    "region": 1,
                    "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                }
            ]
        },
        {
            "data": [
                {
                    "order_id": 444,
                    "weight": 0.23,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00test"]
                },
                {
                    "order_id": 555,
                    "weight": 0.23
                }
            ]
        },
        {
            "data": [
                {
                    "order_id": 777,
                    "weight": 0.23,
                    "region": 22,
                    "delivery_hours": ["09:00-18:00"]
                }
            ]
        },
    ],
    'responses': [
        {
            'status_code': 201,
            'json': {"orders": [{"id": 444}, {"id": 555}, {"id": 666}]}
        },
        {
            'status_code': 400,
            'json': {"validation_error": {"orders": [{"id": 444}, {"id": 555}]}}
        },
        {
            'status_code': 201,
            'json': {"orders": [{"id": 777}]}
        },
    ]
}


courier_get_test_json = {
    'requests': [

    ],
    'responses': [

    ]
}


orders_complete_test_json = {
    'requests': [
        {
            "courier_id": 1,
            "order_id": 444,
            "complete_time": str(datetime.now().timestamp())
        },
        {
            "courier_id": 1,
            "order_id": 0,
            "complete_time": str(datetime.now().timestamp())
        },
    ],
    'responses': [
        {
            'status_code': 200,
            'json': {"order_id": 444}
        },
        {
            'status_code': 400,
            'json': {"err": "Not Found"}
        }
    ]
}


orders_assign_test_json = {
    'requests': [
        {"courier_id": 1}, {"courier_id": 0}, {"courier_id": 2},
    ],
    'responses': [
        {
            'status_code': 200
        },
        {
            'status_code': 400
        },
        {
            'status_code': 200
        },
    ]
}
