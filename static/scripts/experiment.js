var my_node_id;

// Create the agent.
create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {
      my_node_id = resp.node.id;
      get_infos();
    })
    .fail(function (rejection) {
      // A 403 is our signal that it's time to go to the questionnaire
      if (rejection.status === 403) {
        dallinger.allowExit();
        dallinger.goToPage('questionnaire');
      } else {
        dallinger.error(rejection);
      }
    });
};

get_infos = function() {
  dallinger.getInfos(my_node_id)
    .done(function (resp) {
      // console.log(resp)
      sides_switched = Math.random() < 0.5;

      face_current = JSON.parse(resp.infos[0].contents);
      face_proposal = JSON.parse(resp.infos[1].contents);

      if (sides_switched === false) {
        showFace(face_current, "left");
        showFace(face_proposal, "right");
      } else {
        showFace(face_proposal, "left");
        showFace(face_current, "right");
      }
      $(".submit-response").attr('disabled', false);
    });
};

submit_response = function(choice) {
  if (sides_switched === true) {
    choice = 1 - choice;
  }
  $(".submit-response").attr('disabled',true);

  dallinger.post('/choice/' + my_node_id + '/' + choice)
    .then(function () {
      create_agent();
    });
};

showFace = function (face, side) {
  if (side === "left") {
    $("#face_left").html(face["start_happy"]);
  } else if (side === "right") {
    $("#face_right").html(face["start_happy"]);
  }
}

