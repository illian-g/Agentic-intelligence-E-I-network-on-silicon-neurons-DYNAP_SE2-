import unittest

import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from io import StringIO
import samna.dynapse1 as dyn1
from NetworkGenerator import Neuron, NeuronGroup, Synapses, Network, WTA_connections, NetworkGenerator, add_synapses, add_wta_conns 

class AddConnectionsTest(unittest.TestCase):
    """Assume that the neuron-level things work, test the neuron group, synapses, wta, add_connections."""
    
    pre_group = NeuronGroup(1, 0, [36, 60])
    post_group = NeuronGroup(3, 1, [153, 78])

    def test_add_synapses_one2one(self):
        # given
        expected_netgen = NetworkGenerator()
        expected_netgen.add_connection(self.pre_group.neurons[0], self.post_group.neurons[0], dyn1.Dynapse1SynType.AMPA)
        expected_netgen.add_connection(self.pre_group.neurons[1], self.post_group.neurons[1], dyn1.Dynapse1SynType.AMPA)

        # when
        result_netgen = NetworkGenerator()
        syn = Synapses(self.pre_group, self.post_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
        add_synapses(result_netgen, syn)

        # then
        self.assertEqual(expected_netgen.network, result_netgen.network)

    def test_add_synapses_all2all(self):
        # given
        expected_netgen = NetworkGenerator()
        for pre in self.pre_group.neurons:
            for post in self.post_group.neurons:
                expected_netgen.add_connection(pre, post, dyn1.Dynapse1SynType.NMDA)

        # when
        result_netgen = NetworkGenerator()
        syn = Synapses(self.pre_group, self.post_group, dyn1.Dynapse1SynType.NMDA, conn_type='all2all')
        add_synapses(result_netgen, syn)

        # then
        self.assertEqual(expected_netgen.network, result_netgen.network)
    
    def test_add_wta(self):
        # given
        expected_netgen = NetworkGenerator()
        # EI AMPA
        for exc in self.pre_group.neurons:
            for inh in self.post_group.neurons:
                expected_netgen.add_connection(exc, inh, dyn1.Dynapse1SynType.AMPA)

        # IE GABA_B
        for inh in self.post_group.neurons:
            for exc in self.pre_group.neurons:
                expected_netgen.add_connection(inh, exc, dyn1.Dynapse1SynType.GABA_B)

        # EE NMDA
        expected_netgen.add_connection(self.pre_group.neurons[0], self.pre_group.neurons[0], dyn1.Dynapse1SynType.NMDA)
        expected_netgen.add_connection(self.pre_group.neurons[1], self.pre_group.neurons[1], dyn1.Dynapse1SynType.NMDA)

        # when
        result_netgen = NetworkGenerator()
        wta = WTA_connections(self.pre_group, self.post_group, syn_type_ei= dyn1.Dynapse1SynType.AMPA, syn_type_ie=dyn1.Dynapse1SynType.GABA_B, syn_type_ee=dyn1.Dynapse1SynType.NMDA, ee_pres=[0,1], ee_posts=[0,1])
        add_wta_conns(result_netgen, wta)

        # then
        print(expected_netgen.network, result_netgen.network)
        self.assertEqual(expected_netgen.network, result_netgen.network)
    
        
    
if __name__ == "__main__":
    """ execute all tests in module """
    unittest.main()