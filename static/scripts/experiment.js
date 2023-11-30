var my_node_id;
var questions = ["Who looks happier?", "Who looks happier?", 
  "Who looks sadder?", "Who looks sadder?", 
  "Who looks more neutral?", "Who looks more neutral?"];

// Create the agent.
create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {
      my_node_id = resp.node.id;
      if (resp.node.type === "VGMCPAgent") {
        $("h1").html(questions[(resp.node.network_id-1) % 6]);
        get_infos();
      } else {
        deleteNode(my_node_id);
        dallinger.goToPage('instruct-2');
      }
      // switch (resp.node.type) {
      //   case "VGMCPAgent":
      //     get_infos();
      //   default: 
      //     deleteNode(my_node_id);
      //     dallinger.goToPage('experiment2');
      // }
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
    $("#face_left").attr('src', 'data:image/jpeg;base64,' + face["face"]);
  } else if (side === "right") {
    $("#face_right").attr('src', 'data:image/jpeg;base64,' + face["face"]);
  }
}


function deleteNode (my_node_id) {
  dallinger.post('/delete/' + my_node_id)
}