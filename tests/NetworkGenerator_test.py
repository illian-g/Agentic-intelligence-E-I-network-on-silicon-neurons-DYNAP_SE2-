import unittest

import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from NetworkGenerator import Neuron, NeuronGroup 

class NetworkGeneratorTest(unittest.TestCase):
    def test_neuron_group(self):
        # given
        chip1 = 0
        core1 = 0
        nids1 = [101,102,103]
        expected_neurons = []
        for nid in nids1:
            expected_neurons.append(Neuron(chip1,core1,nid))

        # when
        neuron_group = NeuronGroup(chip1,core1,nids1)
        result_neurons = neuron_group.neurons

        # then
        print(str(expected_neurons), str(result_neurons))

        # assert(expected_neurons == result_neurons)
        self.assertEqual(repr(expected_neurons), repr(result_neurons))
        self.assertEqual(str(expected_neurons), str(result_neurons))

        # TODO: how to add self-defined == for a class? then assertEqual can be used?..  not only through __repr__(), right?


        # TODO: independent tests. When 1 attribute changes, the getter should follow.
        # given
        new_chip = 2
        neuron_group.chip_id = new_chip
        expected_neurons = []
        for nid in nids1:
            expected_neurons.append(Neuron(new_chip,core1,nid))

        # when
        result_neurons = neuron_group.neurons

        # then
        print(str(expected_neurons), str(result_neurons))
        self.assertEqual(str(expected_neurons), str(result_neurons))
    
if __name__ == "__main__":
    """ execute all tests in module """
    unittest.main()