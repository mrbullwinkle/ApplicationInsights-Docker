#
# ApplicationInsights-Docker
# Copyright (c) Microsoft Corporation
# All rights reserved.
#
# MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the ""Software""), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import time

__author__ = 'galha'

import unittest
from unittest.mock import patch, MagicMock
from unittest.mock import Mock, mock_open
from appinsights.dockerwrapper import DockerClientWrapper, DockerWrapperError
from appinsights.dockercollector import DockerCollector

class TestDockerCollector(unittest.TestCase):
    def test_collect_and_send(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = ['m1','m2','m3']
        containers = [{'Id':'c1','ikey':'k1'}, {'Id':'c2','ikey':'k2'}, {'Id':'c3','ikey':'k3'}]
        stats = ['s1','s2','s3']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock()
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.return_value = ''
                injector_mock = Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock, 3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                expected_metrics = [{'metric':metric, 'properties': properties} for container in containers for metric in metrics]
                expectedEventsCount = len(containers)*len(metrics)
                self.assertEqual(expectedEventsCount, len(events))
                for sent_event in events:
                    self.assertIn(sent_event ,expected_metrics)

    def test_collect_and_send_dont_send_events_when_no_containers(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = ['m1','m2','m3']
        containers = []
        stats = ['s1','s2','s3']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock(spec=DockerClientWrapper)
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.return_value = ''
                injector_mock = Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock, 3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                self.assertEqual(0, len(events))

    def test_collect_and_send_dont_send_events_when_no_metrics(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = []
        containers = [{'Id':'c1'}, {'Id':'c2'}]
        stats = ['s1','s2']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock(spec=DockerClientWrapper)
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.return_value = ''
                injector_mock=Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock ,3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                self.assertEqual(0, len(events))

    def test_collect_and_send_dont_sends_only_metrics_on_the_sender_container_when_sdk_is_running(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = ['m1','m2','m3']
        containers = [{'Id':'c1'}, {'Id':'c2'}, {'Id':'c3'}]
        stats = ['s1','s2','s3']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock(spec=DockerClientWrapper)
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.return_value = 'InstrumentationKey=ikey'
                injector_mock = Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock,3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                self.assertEqual(3, len(events))
                wrapper_mock.get_stats.call_with(container={'Id':'c1'})
                self.assertEqual(1, wrapper_mock.get_stats.call_count)

    def test_when_docker_wrapper_raises_on_run_commnad_it_assume_there_is_no_sdk_and_send_events(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = ['m1','m2','m3']
        containers = [{'Id':'c1'}]
        stats = ['s1','s2','s3']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock(spec=DockerClientWrapper)
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.side_effect = DockerWrapperError('container is paused')
                injector_mock = Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock, 3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                self.assertEqual(len(metrics), len(events))

    def test_sender_sends_events_even_when_it_has_sdk(self):
        events = []
        properties = {'p1':'v1','p2':'v2'}
        metrics = ['m1','m2','m3']
        containers = [{'Id':'c1'}]
        stats = ['s1','s2','s3']
        host_name = 'host'
        with patch('appinsights.dockerconvertors.get_container_properties') as properties_mock:
            with patch('appinsights.dockerconvertors.convert_to_metrics') as to_metric_mock:
                properties_mock.return_value = properties
                to_metric_mock.return_value = metrics
                wrapper_mock = Mock(spec=DockerClientWrapper)
                wrapper_mock.get_host_name.return_value = host_name
                wrapper_mock.get_containers.return_value = containers
                wrapper_mock.get_stats.return_value = stats
                wrapper_mock.run_command.return_value = 'InstrumentationKey=ikey'
                injector_mock = Mock()
                injector_mock.get_my_container_id.return_value = 'c1'
                collector = DockerCollector(wrapper_mock, injector_mock, 3, lambda x: events.append(x))
                collector.collect_stats_and_send()
                self.assertEqual(len(metrics), len(events))
                self.assertEqual(3, len(events))

    def test_old_container_is_not_removed_immediately(self):
        new_containers = [{'Id':'c2','ikey':'k2', 'unregistered': None}]
        current_containers = {'c1': {'Id':'c1','ikey':'k1', 'unregistered': time.time()}}

        updated_containers = DockerCollector.remove_old_containers(current_containers, new_containers)

        self.assertEqual(current_containers['c1']['Id'], updated_containers['c1']['Id'])

    def test_old_container_is_removed_after_threshold(self):
        new_containers = [{'Id':'c2','ikey':'k2', 'unregistered': None}]
        current_containers = {'c1': {'Id':'c1','ikey':'k1', 'unregistered': time.time() - 70}}

        updated_containers = DockerCollector.remove_old_containers(current_containers, new_containers)

        self.assertTrue(len(updated_containers) == 0)
