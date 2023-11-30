"""Monte Carlo Markov Chains with people."""
import random
import time
from operator import attrgetter

from flask import Response
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from dallinger.bots import BotBase
from dallinger.experiment import Experiment, experiment_route
from dallinger.networks import Chain
from dallinger.nodes import ReplicatorAgent


class VGMCP(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session=None):
        """Call the same function in the super (see experiments.py in dallinger).

        The models module is imported here because it must be imported at
        runtime.

        A few properties are then overwritten.

        Finally, setup() is called.
        """
        super(VGMCP, self).__init__(session)
        from . import models

        self.models = models
        self.task = "VAE-guided MCMCP for Facial Expression"
        self.experiment_repeats = 2  # how many participants

        self.trials_MCMCP = 6*2  # six chains each person, n trials per chain
        self.probe_images = 5
        self.mapping_images = 11*11*11
        if session:
            self.setup()

    def create_node(self, network, participant):
        """Create a node for a participant."""
        if network.type == "chain":
            return self.models.VGMCPAgent(network=network, participant=participant)
        elif network.role[0] == "P":
            return self.models.ProbeAgent(network=network, participant=participant) 
        elif network.role[0] == "M":
            return self.models.MappingAgent(network=network, participant=participant) 

    def setup(self):
        """Create the networks if they don't already exist."""
        if not self.networks():
            # add chain network for MCMCP
            for participant_id in range(1, self.experiment_repeats+1):

                Chain_happy_1 = self.create_network("Chain")
                Chain_happy_1.role = f"Chain_happy_p{participant_id}"
                self.session.add(Chain_happy_1)
                Chain_happy_2 = self.create_network("Chain")
                Chain_happy_2.role = f"Chain_happy_p{participant_id}"
                self.session.add(Chain_happy_2)

                Chain_sad_1 = self.create_network("Chain")
                Chain_sad_1.role = f"Chain_sad_p{participant_id}"
                self.session.add(Chain_sad_1)
                Chain_sad_2 = self.create_network("Chain")
                Chain_sad_2.role = f"Chain_sad_p{participant_id}"
                self.session.add(Chain_sad_2)

                Chain_neu_1 = self.create_network("Chain")
                Chain_neu_1.role = f"Chain_neu_p{participant_id}"
                self.session.add(Chain_neu_1)
                Chain_neu_2 = self.create_network("Chain")
                Chain_neu_2.role = f"Chain_neu_p{participant_id}"
                self.session.add(Chain_neu_2)

            # add empty network for image rating (probe trials)
            for image_id in range(1, self.probe_images+1):
                network = self.create_network("Empty")
                network.role = f"Probe_{image_id}"
                self.session.add(network)

            # add empty network for mapping trials
            for image_id in range(1, self.mapping_images+1):
                network = self.create_network("Empty")
                network.role = f"Mapping_{image_id}"
                self.session.add(network)

            # add source for each network
            for net in self.networks():
                if net.type == "chain":
                    self.models.vgmcpSource(network=net)
                elif net.type == "empty":
                    self.models.rateSource(network=net)
            self.session.commit()

    def create_network(self, type="Empty"):
        """Create a new network."""
        if type == "Chain":
            return Chain(max_size=10000)
        elif type == "Empty":
            return self.models.Empty_custom(max_size=10000)

    def get_network_for_participant(self, participant):
        n_nodes = len(participant.nodes(failed="all"))

        if n_nodes < self.trials_MCMCP:  # seuqence of conditions (happy->sad->neutral)
            if n_nodes < self.trials_MCMCP/3:
                return random.choice(self.networks(role=f"Chain_happy_p{participant.id}")) # random.choice(networks)
            elif n_nodes < self.trials_MCMCP*2/3:
                return random.choice(self.networks(role=f"Chain_sad_p{participant.id}"))
            else:
                return random.choice(self.networks(role=f"Chain_neu_p{participant.id}"))
        elif n_nodes < self.trials_MCMCP + self.probe_images:  # need more randomness
            return self.networks(role=f"Probe_{n_nodes - self.trials_MCMCP + 1}")[0]
        elif n_nodes < self.trials_MCMCP + self.probe_images + self.mapping_images/121:
            return random.choice([net for net in self.networks() if net.role[0] == "M" and len(net.nodes(failed="all")) <= 4])
            # return self.networks(role=f"Mapping_{n_nodes - self.trials_MCMCP - self.probe_images + 1}")[0]
        else:
            return None

    def add_node_to_network(self, node, network):
        """When a node is created it is added to the chain (see Chain in networks.py)
        and it receives any transmissions."""
        network.add_node(node)
        parent = node.neighbors(direction="from")[0]
        parent.transmit()
        node.receive()

    def data_check(self, participant):
        """Make sure each trial contains exactly one chosen info."""
        infos = participant.infos()
        # return len([info for info in infos if info.chosen]) * 2 == len(infos)
        return True

    @experiment_route("/choice/<int:node_id>/<int:choice>", methods=["POST"])
    @classmethod
    def choice(cls, node_id, choice):
        from .models import VGMCPAgent
        from dallinger import db

        try:
            exp = VGMCP(db.session)
            node = VGMCPAgent.query.get(node_id)
            infos = node.infos()

            if choice == 0:
                info = min(infos, key=attrgetter("id"))
            elif choice == 1:
                info = max(infos, key=attrgetter("id"))
            else:
                raise ValueError("Choice must be 1 or 0")

            info.chosen = True
            exp.save()

            return Response(status=200, mimetype="application/json")
        except Exception:
            return Response(status=403, mimetype="application/json")


    @experiment_route("/delete/<int:node_id>", methods=["POST"])
    @classmethod
    def delete(cls, node_id):
        # Delete the node
        from dallinger import db

        node = ReplicatorAgent.query.get(node_id)
        db.session.delete(node)
        db.session.commit()
        return Response(status=200, mimetype="application/json")

    @experiment_route("/probe/<int:node_id>/<choice>/<int:rating>", methods=["POST"])
    @classmethod
    def probe(cls, node_id, choice, rating):
        from dallinger import db

        try:
            exp = VGMCP(db.session)
            node = ReplicatorAgent.query.get(node_id)
            info = node.infos()[0]

            info.rating = rating
            info.choice = choice
            exp.save()

            return Response(status=200, mimetype="application/json")
        except Exception:
            return Response(status=403, mimetype="application/json")

    @experiment_route("/mapping/<int:node_id>/<int:rating1>/<int:rating2>", methods=["POST"])
    @classmethod
    def mapping(cls, node_id, rating1, rating2):
        from dallinger import db

        try:
            exp = VGMCP(db.session)
            node = ReplicatorAgent.query.get(node_id)
            info = node.infos()[0]

            info.mapping1 = rating1
            info.mapping2 = rating2
            exp.save()

            return Response(status=200, mimetype="application/json")
        except Exception:
            return Response(status=403, mimetype="application/json")


class Bot(BotBase):
    """Bot tasks for experiment participation"""

    def participate(self):
        """Finish reading and send text"""
        try:
            while True:
                left = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "left_button"))
                )
                right = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "right_button"))
                )

                random.choice((left, right)).click()
                time.sleep(1.0)
        except TimeoutException:
            return False
