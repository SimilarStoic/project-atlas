var q = function (selector) {
  return document.querySelector(selector);
};

function screen(name) {
  document.querySelectorAll(".screen").forEach(function (element) {
    element.classList.toggle("active", element.id === name);
  });
  document.querySelectorAll("[data-screen]").forEach(function (element) {
    element.classList.toggle("active", element.dataset.screen === name);
  });
  q("#title").textContent = {
    command: "Good morning, Jude.",
    discover: "Discover the next useful story.",
    workspace: "Shape the production-ready package.",
    chat: "Ask, steer, investigate.",
  }[name];
}

document.querySelectorAll("[data-screen]").forEach(function (element) {
  element.onclick = function () {
    screen(element.dataset.screen);
  };
});

function say(text) {
  q("#toast").textContent = text;
  q("#toast").classList.add("show");
  setTimeout(function () {
    q("#toast").classList.remove("show");
  }, 1800);
}

function opportunity(item) {
  return (
    '<article class="opportunity"><span class="score">' +
    item.score +
    '</span><div><label>' +
    item.pillar +
    "</label><h3>" +
    item.topic +
    "</h3><p>" +
    item.why_now +
    '</p><span class="tag">' +
    item.evidence_quality +
    '</span><span class="tag">Risk: ' +
    item.risk +
    '</span><span class="tag">Visual: ' +
    item.visual_potential +
    "</span></div><div><b>Suggested angle</b><p>" +
    item.suggested_angle +
    "</p><b>Viewer benefit</b><p>" +
    item.viewer_benefit +
    "</p><p><b>Portfolio:</b> " +
    item.portfolio_relevance +
    '</p></div><div class="actions"><button>Approve</button><button>Modify</button><button>Reject</button><button>Ask Atlas</button></div></article>'
  );
}

function researchEvidence(research) {
  if (!research) {
    return "";
  }
  var claims = research.claims
    .map(function (claim) {
      var sources = claim.evidence
        .map(function (evidence) {
          var source = evidence.source;
          var reference = evidence.reference ? " · " + evidence.reference : "";
          return (
            "<li><b>" +
            evidence.stance +
            "</b> · <a href=\"" +
            source.url +
            '\" target="_blank" rel="noreferrer">' +
            source.publisher +
            ": " +
            source.title +
            "</a>" +
            reference +
            "<br><small>" +
            evidence.notes +
            "</small></li>"
          );
        })
        .join("");
      return (
        '<div class="pack"><label>' +
        claim.claim_type +
        " · " +
        claim.verification_status +
        "</label><h3>" +
        claim.text +
        "</h3><p>Risk: " +
        claim.risk_level +
        " · Freshness: " +
        claim.freshness_type +
        "</p><p>" +
        claim.verification_notes +
        "</p><ul class=\"qa\">" +
        sources +
        "</ul></div>"
      );
    })
    .join("");
  return '<div class="pack"><label>CLAIMS &amp; EVIDENCE · PERSISTED RESEARCH</label>' + claims + "</div>";
}

function editorialAngle(content) {
  var angle = content.editorial_angle;
  if (!angle) {
    return '<div class="pack"><label>EDITORIAL ANGLE</label><h3>' + content.selected_angle + "</h3></div>";
  }
  var takeaways = angle.key_takeaways
    .map(function (takeaway) {
      return "<li>" + takeaway + "</li>";
    })
    .join("");
  var claims = angle.claims
    .map(function (claim) {
      return "<li><b>" + claim.role + "</b> · " + claim.text + "</li>";
    })
    .join("");
  return (
    '<div class="pack"><label>EDITORIAL ANGLE · PERSISTED</label><h3>' +
    angle.working_title +
    "</h3><p><b>Thesis</b><br>" +
    angle.thesis +
    "</p><p><b>Audience promise</b><br>" +
    angle.audience_promise +
    "</p><p><b>Framing</b><br>" +
    angle.framing +
    '</p><p><b>Intended takeaways</b></p><ul class="qa">' +
    takeaways +
    '</ul><p><b>Grounded claims</b></p><ul class="qa">' +
    claims +
    "</ul></div>"
  );
}

function contentPiece(content) {
  var piece = content.content_piece;
  if (!piece) {
    return "";
  }
  var script = piece.latest_script;
  return (
    '<div class="pack"><label>CONTENT PIECE · PERSISTED</label><h3>' +
    piece.working_title +
    "</h3><p><b>Format</b><br>" +
    piece.format_key +
    "</p>" +
    (script ? "<p><b>Latest narration version</b><br>v" + script.version + "</p>" : "") +
    "</div>"
  );
}

function visualPlan(content) {
  var plan = content.visual_plan;
  if (!plan) {
    return "";
  }
  var scenes = plan.scenes
    .map(function (scene) {
      var hamsterAction = scene.hamster_action
        ? "<p><b>Hamster action</b><br>" + scene.hamster_action + "</p>"
        : "";
      var onScreenText = scene.on_screen_text
        ? "<p><b>Supporting on-screen text</b><br>" + scene.on_screen_text + "</p>"
        : "";
      var transition = scene.transition_note
        ? "<p><b>Transition</b><br>" + scene.transition_note + "</p>"
        : "";
      return (
        '<li><b>Scene ' +
        scene.sequence +
        "</b> · " +
        scene.narration_excerpt +
        "<br><small>" +
        scene.visual_intent +
        "</small>" +
        hamsterAction +
        onScreenText +
        transition +
        "</li>"
      );
    })
    .join("");
  return (
    '<div class="pack"><label>VISUAL PLAN &amp; SCENES · PERSISTED</label><p><b>Direction</b><br>' +
    plan.visual_direction +
    '</p><p><b>Ordered scenes</b></p><ul class="qa">' +
    scenes +
    "</ul></div>"
  );
}

function bindActions() {
  document.querySelectorAll(".actions button").forEach(function (element) {
    element.onclick = function () {
      if (element.textContent === "Ask Atlas") {
        screen("chat");
      }
      say(element.textContent + " is recorded locally for this demo.");
    };
  });
}

function pack(content) {
  q("#content-title").textContent = content.title;
  var scenePlanCompatibility = content.scene_plan
    ? '<div class="pack"><label>SCENE PLAN COMPATIBILITY · PERSISTED</label><p>' +
      content.scene_plan +
      "</p></div>"
    : "";
  var qa = content.qa
    .map(function (item) {
      return (
        "<li><span>" +
        item.label +
        '</span><b class="' +
        (item.state === "Passed" ? "pass" : "review") +
        '">' +
        item.state +
        "</b></li>"
      );
    })
    .join("");
  var research = content.research;
  var version = research ? " v" + research.version : "";
  q("#workspace").innerHTML =
    '<div class="pack"><label>LIFECYCLE</label><p>' +
    content.lifecycle.join(" → ") +
    '</p></div><div class="workspace"><div><div class="pack"><label>RESEARCH PACK' +
    version +
    "</label><p>" +
    content.research_summary +
    '</p><div class="facts"><div><b>' +
    content.claim_count +
    '</b><small>mapped claims</small></div><div><b>' +
    content.source_count +
    '</b><small>sources</small></div><div><b>Medium</b><small>risk</small></div></div></div>' +
    researchEvidence(research) +
    editorialAngle(content) +
    contentPiece(content) +
    '<div class="pack"><label>SCRIPT / NARRATION · PERSISTED</label><p>' +
    content.script +
    "</p></div>" +
    visualPlan(content) +
    scenePlanCompatibility +
    '</div><div><div class="pack"><label>CONTENT CONTEXT</label><p><b>Audience</b><br>' +
    content.target_audience +
    '</p><p><b>Pillar</b><br>' +
    content.pillar +
    '</p><p><b>Risk</b><br>' +
    content.risk +
    '</p></div><div class="pack"><label>QA STATUS</label><ul class="qa">' +
    qa +
    '</ul><div class="actions"><button>Approve</button><button>Request changes</button><button>Reject</button></div></div></div></div>';
  bindActions();
}

Promise.all([
  fetch("/api/demo/opportunities").then(function (response) {
    return response.json();
  }),
  fetch("/api/demo/content").then(function (response) {
    return response.json();
  }),
])
  .then(function (data) {
    q("#opportunities").innerHTML = data[0].opportunities.map(opportunity).join("");
    var activity = q("#activity");
    if (activity) {
      activity.innerHTML = data[1].activity
        .map(function (item) {
          return "<li><b>" + item.time + "</b> " + item.text + "</li>";
        })
        .join("");
    }
    pack(data[1].content);
    bindActions();
  })
  .catch(function () {
    say("Demo data could not be loaded.");
  });

function ask(text) {
  if (!text.trim()) {
    return;
  }
  q("#messages").innerHTML += '<p class="user">' + text + "</p>";
  q("#input").value = "";
  fetch("/api/demo/chat?message=" + encodeURIComponent(text))
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      q("#messages").innerHTML += '<p class="atlas">' + data.reply + "</p>";
    });
}

q("#chat-form").onsubmit = function (event) {
  event.preventDefault();
  ask(q("#input").value);
};
document.querySelectorAll("#suggestions button").forEach(function (element) {
  element.onclick = function () {
    ask(element.textContent);
  };
});
