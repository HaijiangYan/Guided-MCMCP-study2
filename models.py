from numpy import random
import json
import requests
from sqlalchemy import Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast

from dallinger.models import Info
from dallinger.models import Transformation
from dallinger.nodes import Agent, Source, ReplicatorAgent
from dallinger.networks import Empty

class Empty_custom(Empty):

    __mapper_args__ = {"polymorphic_identity": "empty"}

    def add_node(self, node):
        """Connect new nodes to the source."""
        source = [n for n in self.nodes() if isinstance(n, Source)][0]
        source.connect(whom=node)


class ProbeAgent(ReplicatorAgent):

    __mapper_args__ = {"polymorphic_identity": "ProbeAgent"}


class MappingAgent(ReplicatorAgent):

    __mapper_args__ = {"polymorphic_identity": "MappingAgent"}


class VGMCPAgent(Agent):

    __mapper_args__ = {"polymorphic_identity": "VGMCPAgent"}

    def update(self, infos):
        info = infos[0]
        self.replicate(info)
        new_info = FaceInfo(origin=self, contents=info.perturbed_contents())
        # Perturbation(info_in=info, info_out=new_info)

    def _what(self):
        infos = self.infos()
        return [i for i in infos if i.chosen][0]


class vgmcpSource(Source):
    """A source that transmits facial expression."""

    __mapper_args__ = {"polymorphic_identity": "vgmcp_Source"}

    # start points of Chains of happy, sad and neutral
    startPoint = {
        "happy": [0, 0, 0],
        "sad": [0.1, 1.5, 0],
        "neu": [-1.5, 4.5, 0],
    }

    def create_information(self):
        """Create a new Info.

        transmit() -> _what() -> create_information().
        """
        data = {}
        key = self.network.role.split("_")[1]
        cov = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        sample = random.multivariate_normal(self.startPoint[key], cov, 1)
        data["face"] = requests.post('http://212.71.252.12/generate', json={"data": sample.tolist()}).json()
        data["loc"] = sample.squeeze().tolist()

        return FaceInfo(origin=self, contents=json.dumps(data))


class FaceInfo(Info):
    """An Info that can be chosen."""

    __mapper_args__ = {"polymorphic_identity": "vector_info"}

    @hybrid_property
    def chosen(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return bool(self.property1)
        except TypeError:
            return None

    @chosen.setter
    def chosen(self, chosen):
        """Assign chosen to property1."""
        self.property1 = repr(chosen)

    @chosen.expression
    def chosen(self):
        """Retrieve chosen via property1."""
        return cast(self.property1, Boolean)

    def perturbed_contents(self):
        """Perturb the given face."""
        data = json.loads(self.contents)
        cov = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        sample = random.multivariate_normal(data["loc"], cov, 1)
        data["face"] = requests.post('http://212.71.252.12/generate', json={"data": sample.tolist()}).json()
        data["loc"] = sample.squeeze().tolist()
        return json.dumps(data)


class rateSource(Source):
    """A source that transmits facial expression."""

    __mapper_args__ = {"polymorphic_identity": "rate_source"}

    def _what(self):
        """What to transmit by default."""
        data = {}
        if self.network.role[0] == "P": # "probe"
            idx = int(self.network.role.split("_")[-1])
            cov = [[7, 0, 0], [0, 7, 0], [0, 0, 7]]
            loc = random.multivariate_normal([0, 0, 0], cov, 1)
            data["image"] = requests.post('http://212.71.252.12/generate', json={"data": loc.tolist()}).json()
        elif self.network.role[0] == "M": # "mapping"
            idx = int(self.network.role.split("_")[-1])
            loc = [[-5 + ((idx-1)//121), -5 + (((idx-1)%121)//11), -5 + (idx-1)%11]]
            data["image"] = requests.post('http://212.71.252.12/generate', json={"data": loc}).json()

        return rateInfo(origin=self, contents=json.dumps(data))


class rateInfo(Info):
    """An Info that can be chosen."""

    __mapper_args__ = {"polymorphic_identity": "rate_info"}

    @hybrid_property
    def rating(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return int(self.property1)
        except TypeError:
            return None

    @rating.setter
    def rating(self, rating):
        """Assign chosen to property1."""
        self.property1 = repr(rating)

    @rating.expression
    def rating(self):
        """Retrieve chosen via property1."""
        return cast(self.property1, int)

    @hybrid_property
    def choice(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return str(self.property2)
        except TypeError:
            return None

    @choice.setter
    def choice(self, choice):
        """Assign chosen to property1."""
        self.property2 = repr(choice)

    @choice.expression
    def choice(self):
        """Retrieve chosen via property1."""
        return cast(self.property2, str)

    @hybrid_property
    def mapping1(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return int(self.property3)
        except TypeError:
            return None

    @mapping1.setter
    def mapping1(self, mapping1):
        """Assign chosen to property1."""
        self.property3 = repr(mapping1)

    @mapping1.expression
    def mapping1(self):
        """Retrieve chosen via property1."""
        return cast(self.property3, int)

    @hybrid_property
    def mapping2(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return int(self.property4)
        except TypeError:
            return None

    @mapping2.setter
    def mapping2(self, mapping2):
        """Assign chosen to property1."""
        self.property4 = repr(mapping2)

    @mapping2.expression
    def mapping2(self):
        """Retrieve chosen via property1."""
        return cast(self.property4, int)


# class Perturbation(Transformation):
#     """A perturbation is a transformation that perturbs the contents."""

#     __mapper_args__ = {"polymorphic_identity": "perturbation"}
