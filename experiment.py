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
        self.experiment_repeats = 1
        self.trials_per_participant = 10
        if session:
            self.setup()

    def create_node(self, network, participant):
        """Create a node for a participant."""
        return self.models.VGMCPAgent(network=network, participant=participant)

    def setup(self):
        """Setup the networks."""
        # if there is no network when query:
        if not self.networks():  
            super(VGMCP, self).setup()
            for net in self.networks():
                self.models.FaceSource(network=net)
            self.session.commit()

    def create_network(self):
        """Create a new network."""
        return Chain(max_size=10000)

    def get_network_for_participant(self, participant):
        if len(participant.nodes(failed="all")) < self.trials_per_participant:
            return self.networks()[0]
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
        return len([info for info in infos if info.chosen]) * 2 == len(infos)

    @experiment_route("/choice/<int:node_id>/<int:choice>", methods=["POST"])
    @classmethod
    def choice(cls, node_id, choice):
        from .models import Agent
        from dallinger import db

        try:
            exp = VGMCP(db.session)
            node = Agent.query.get(node_id)
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