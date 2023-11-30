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
      face = JSON.parse(resp.infos[0].contents);
      showFace(face);

      $("button").attr('disabled', false);

    });
};

submit_response = function() {

  $("button").attr('disabled', true);

  var rating1 = $('#ratingSlider1');
  var rating2 = $('#ratingSlider2');

  dallinger.post('/mapping/' + my_node_id + '/' + rating1.val() + '/' + rating2.val())
    .then(function () {
      rating1.val(0);
      rating2.val(0);
      $('span').text(0);
      create_agent();
    });
};

showFace = function (face) {
  $("#face_mapping").attr('src', 'data:image/jpeg;base64,' + face["image"]);
}
