#    Copyright 2018 Rackspace, US Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
statuses = {
    'loadbalancer':
        {
            'listeners': [
                {'l7policies': [
                    {
                        'id': 'ce4685c8-3d0a-4692-8147-5397fe1658d4',
                        'rules': [
                            {'id': 'ed41a098-9749-4c2f-a5d8-f7607702dc08'}
                        ]
                    }
                ],
                    'id': '731e76c5-2c82-4bf0-9ce4-33dea507c019',
                }],
            'pools': [
                {
                    'healthmonitor': {
                        'id': '3d2c2d85-a497-40b5-a1cb-c283f7cc01ab',
                    },
                    'members': [
                        {'id': 'e9bae5cf-3804-4579-807b-bccd95566881'}
                    ],
                    'id': '5055adc1-0f47-4c6b-bcb7-43e742af2308',
                }],
            'id': 'ab4849b6-af68-4f14-9498-9e90abb6ca61',
        }
}


class Statuses(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self.statuses = kwargs
