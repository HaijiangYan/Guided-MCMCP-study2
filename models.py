from numpy import random
import json
from sqlalchemy import Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast

from dallinger.models import Info
from dallinger.models import Transformation
from dallinger.nodes import Agent
from dallinger.nodes import Source


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


class FaceSource(Source):
    """A source that transmits facial expression."""

    __mapper_args__ = {"polymorphic_identity": "face_source"}

    def create_information(self):
        """Create a new Info.

        transmit() -> _what() -> create_information().
        """
        return FaceInfo(origin=self, contents=None)


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

    properties = {
        "start_happy": [0, 0, 0],
        "start_sad": [0.1, 1.5, 0],
        "start_another": [-1.5, 4.5, 0],
    }

    def __init__(self, origin, contents=None, **kwargs):
        if contents is None:
            data = {}
            for prop, prop_loc in self.properties.items():
                if prop == "start_happy":
                    data[prop] = prop_loc
            contents = json.dumps(data)

        super(FaceInfo, self).__init__(origin, contents, **kwargs)

    def perturbed_contents(self):
        """Perturb the given face."""
        face = json.loads(self.contents)
        cov = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        for prop, prop_loc in face.items():
            face[prop] = random.multivariate_normal(prop_loc, cov, 1).squeeze().tolist()
        print(face)
        return json.dumps(face)


class Perturbation(Transformation):
    """A perturbation is a transformation that perturbs the contents."""

    __mapper_args__ = {"polymorphic_identity": "perturbation"}
