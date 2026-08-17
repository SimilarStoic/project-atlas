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
  var subjects = item.subjects
    .map(function (subject) {
      return subject.name + " · " + subject.relationship_role;
    })
    .join(" · ");
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
    '</p><p><b>Subjects:</b> ' +
    subjects +
    '</p></div><div class="actions"><button class="open-idea-gate" data-opportunity-id="' +
    item.id +
    '">Review at Idea Gate</button></div></article>'
  );
}

function snapshotReview(snapshot) {
  var review = snapshot.review_payload;
  var opportunity = review.opportunity;
  var subjects = review.subjects
    .map(function (subject) {
      return (
        "<li>" +
        subject.name +
        " · " +
        subject.slug +
        " · " +
        subject.relationship_role +
        "<br><small>" +
        subject.id +
        "</small></li>"
      );
    })
    .join("");
  var context = review.review_context;
  return (
    '<article class="pack idea-gate-review" data-opportunity-id="' +
    snapshot.opportunity_id +
    '"><label>IDEA GATE · FROZEN REVIEW SNAPSHOT</label><h3>' +
    opportunity.title +
    "</h3><p>" +
    opportunity.summary +
    "</p><p><b>Why now</b><br>" +
    opportunity.why_now +
    "</p><p><b>Score</b><br>" +
    opportunity.score +
    "</p><p><b>Atlas recommendation</b><br>" +
    context.atlas_recommendation +
    "</p><p><b>Risk</b><br>" +
    context.material_risk +
    "</p><p><b>Evidence quality</b><br>" +
    context.evidence_quality +
    "</p><p><b>Portfolio relevance</b><br>" +
    context.portfolio_relevance +
    "</p><p><b>Visual potential</b><br>" +
    context.visual_potential +
    "</p><p><b>Display pillar</b><br>" +
    context.display_pillar +
    '</p><p><b>Subjects</b></p><ul class="qa">' +
    subjects +
    '</ul><p><small>Snapshot ' +
    snapshot.id +
    " · " +
    snapshot.created_at +
    '</small></p><label>FOUNDER COMMENT / STEER DIRECTION</label><textarea id="idea-gate-comment" placeholder="Optional for Proceed or Reject; required for Steer."></textarea><div class="actions"><button class="record-idea-gate-decision" data-snapshot-id="' +
    snapshot.id +
    '" data-outcome="Proceed">Proceed</button><button class="record-idea-gate-decision subtle" data-snapshot-id="' +
    snapshot.id +
    '" data-outcome="Reject">Reject</button><button class="record-idea-gate-decision" data-snapshot-id="' +
    snapshot.id +
    '" data-outcome="Steer">Steer</button></div></article>'
  );
}

function historyView(payload) {
  if (!payload.history.length) {
    return "";
  }
  return (
    '<div class="pack idea-gate-history"><label>IDEA GATE HISTORY · PERSISTED</label><ul class="qa">' +
    payload.history
      .map(function (item) {
        var decision = item.decision;
        var decisionText = decision
          ? decision.outcome +
            (decision.founder_direction ? " · " + decision.founder_direction : "") +
            (decision.founder_comment ? " · " + decision.founder_comment : "")
          : "Awaiting founder decision";
        return (
          "<li><b>" +
          item.snapshot.review_payload.opportunity.title +
          "</b><br><small>" +
          item.snapshot.id +
          " · " +
          decisionText +
          "</small></li>"
        );
      })
      .join("") +
    "</ul></div>"
  );
}

function requestJson(url, options) {
  return fetch(url, options).then(function (response) {
    return response.json().then(function (payload) {
      if (!response.ok) {
        throw new Error(payload.error || "Atlas could not complete the Idea Gate action.");
      }
      return payload;
    });
  });
}

function refreshIdeaGateHistory(opportunityId) {
  return requestJson(
    "/api/opportunities/" + encodeURIComponent(opportunityId) + "/idea-gate-history"
  ).then(function (payload) {
    q("#idea-gate-history").innerHTML = historyView(payload);
  });
}

function bindIdeaGateActions() {
  document.querySelectorAll(".open-idea-gate").forEach(function (element) {
    element.onclick = function () {
      element.disabled = true;
      requestJson(
        "/api/opportunities/" +
          encodeURIComponent(element.dataset.opportunityId) +
          "/idea-gate-review-snapshots",
        { method: "POST" }
      )
        .then(function (payload) {
          q("#idea-gate-review").innerHTML = snapshotReview(payload.snapshot);
          return refreshIdeaGateHistory(payload.snapshot.opportunity_id).then(function () {
            bindIdeaGateActions();
            say("Frozen Idea Gate review snapshot created.");
          });
        })
        .catch(function (error) {
          say(error.message);
          element.disabled = false;
        });
    };
  });
  document.querySelectorAll(".record-idea-gate-decision").forEach(function (element) {
    element.onclick = function () {
      var text = q("#idea-gate-comment").value;
      var outcome = element.dataset.outcome;
      if (outcome === "Steer" && !text.trim()) {
        say("Steer requires founder direction.");
        return;
      }
      element.disabled = true;
      requestJson(
        "/api/idea-gate-review-snapshots/" +
          encodeURIComponent(element.dataset.snapshotId) +
          "/decisions",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            outcome: outcome,
            founder_comment: outcome === "Steer" ? null : text || null,
            founder_direction: outcome === "Steer" ? text : null,
          }),
        }
      )
        .then(function (payload) {
          var review = q("#idea-gate-review article");
          var opportunityId = review.dataset.opportunityId;
          q("#idea-gate-review").innerHTML = "";
          say("Idea Gate " + payload.decision.outcome + " decision persisted.");
          return refreshIdeaGateHistory(opportunityId);
        })
        .catch(function (error) {
          say(error.message);
          element.disabled = false;
        });
    };
  });
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
  var style = content.visual_style;
  var visualStyle = style
    ? '<p><b>Visual style</b><br>' + style.name + " · v" + style.version + "</p>"
    : "";
  var scenes = plan.scenes
    .map(function (scene) {
      var assetSpecs = scene.asset_specs
        .map(function (assetSpec) {
          var continuity = assetSpec.continuity_key
            ? "<p><b>Continuity key</b><br>" + assetSpec.continuity_key + "</p>"
            : "";
          var characterProfile = assetSpec.character_profile
            ? "<p><b>Character identity</b><br>" +
              assetSpec.character_profile.name +
              " Â· v" +
              assetSpec.character_profile.version +
              "<br><small>" +
              assetSpec.character_profile.identity_description +
              "</small></p>"
            : "";
          var registeredAssets = assetSpec.assets.length
            ? "<p><b>Registered assets</b><br>" + assetSpec.assets.length + "</p>"
            : "<p><b>Registered assets</b><br>0</p>";
          var executions = assetSpec.generation_executions || [];
          var latestExecution = executions.length ? executions[executions.length - 1] : null;
          var executionStatus = latestExecution
            ? "<p><b>Latest generation</b><br>" +
              latestExecution.outcome +
              " Â· " +
              latestExecution.generator_key +
              (latestExecution.model_key ? " / " + latestExecution.model_key : "") +
              (latestExecution.error_message ? "<br><small>" + latestExecution.error_message + "</small>" : "") +
              (latestExecution.character_profile
                ? "<br><small>Character: " +
                  latestExecution.character_profile.name +
                  " Â· v" +
                  latestExecution.character_profile.version +
                  "</small>"
                : "") +
              "</p>"
            : "";
          var generateAction = assetSpec.generation_supported
            ? '<button class="generate-asset" data-asset-spec-id="' + assetSpec.id + '">' +
              (assetSpec.character_profile ? "Generate grounded" : "Generate") +
              "</button>"
            : "";
          var bootstrapAction = assetSpec.bootstrap_reference_generation_available
            ? '<button class="bootstrap-reference-asset" data-asset-spec-id="' + assetSpec.id + '">Bootstrap reference candidate</button>'
            : "";
          return (
            '<li><b>' +
            assetSpec.asset_type +
            "</b> · " +
            assetSpec.purpose +
            "<br><small>" +
            assetSpec.description +
            "</small><p><b>Canonical generation prompt</b><br>" +
            assetSpec.generation_prompt +
            "</p>" +
            continuity +
            characterProfile +
            registeredAssets +
            executionStatus +
            generateAction +
            bootstrapAction +
            "</li>"
          );
        })
        .join("");
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
        (assetSpecs
          ? '<p><b>Asset requirements · persisted</b></p><ul class="qa">' +
            assetSpecs +
            "</ul>"
          : "") +
        "</li>"
      );
    })
    .join("");
  return (
    '<div class="pack"><label>VISUAL PLAN &amp; SCENES · PERSISTED</label><p><b>Direction</b><br>' +
    plan.visual_direction +
    "</p>" +
    visualStyle +
    '<p><b>Ordered scenes</b></p><ul class="qa">' +
    scenes +
    "</ul></div>"
  );
}

var referenceSelection = [];

function referenceAssetCard(asset, selectable) {
  var execution = asset.generation_execution;
  var profile = execution.character_profile;
  var selector = selectable
    ? '<label class="reference-select"><input type="checkbox" class="reference-candidate" data-asset-id="' +
      asset.id +
      '"> Add to reference set</label>'
    : "";
  return (
    '<article class="reference-asset"><img src="/api/assets/' +
    encodeURIComponent(asset.id) +
    '/content" alt="Generated SimilarStoic hamster candidate"><div><b>Asset v' +
    asset.version +
    "</b><br><small>" +
    asset.id +
    "</small><p>Execution: " +
    execution.id +
    "<br>Provider/model: " +
    (execution.provider_key || "unknown") +
    " / " +
    (execution.model_key || "unknown") +
    "<br>Character: " +
    profile.name +
    " · v" +
    profile.version +
    "</p><small>Digest: " +
    asset.content_digest +
    "</small>" +
    selector +
    "</div></article>"
  );
}

function characterReferenceReview(review) {
  if (!review || !review.character_profile) {
    return "";
  }
  var candidates = review.eligible_assets.length
    ? review.eligible_assets.map(function (asset) { return referenceAssetCard(asset, true); }).join("")
    : "<p>No eligible generated hamster Assets yet. Before the first reference set, explicitly bootstrap a scene-derived character reference candidate.</p>";
  var existingSets = review.reference_sets.length
    ? review.reference_sets
        .map(function (set) {
          return (
            '<div class="reference-set"><b>Reference set v' +
            set.version +
            "</b><br><small>" +
            set.id +
            '</small><div class="reference-assets">' +
            set.members
              .map(function (member) {
                return '<div><small>Position ' + member.position + "</small>" + referenceAssetCard(member.asset, false) + "</div>";
              })
              .join("") +
            "</div></div>"
          );
        })
        .join("")
    : "<p>No canonical visual reference set has been created.</p>";
  return (
    '<div class="pack"><label>CANONICAL VISUAL REFERENCE BASIS · PERSISTED</label><h3>' +
    review.character_profile.name +
    " · v" +
    review.character_profile.version +
    '</h3><p>Choose existing eligible, scene-derived hamster Assets in the order they should form one immutable visual reference basis. At character-generation time, Atlas resolves the highest version for this CharacterProfile; it does not guarantee consistency.</p><div class="reference-assets">' +
    candidates +
    '</div><div class="actions"><button class="create-reference-set" data-character-profile-id="' +
    review.character_profile.id +
    '">Create immutable reference set</button></div><p><b>Existing reference sets</b></p>' +
    existingSets +
    "</div>"
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

function bindGenerationActions() {
  document.querySelectorAll(".generate-asset").forEach(function (element) {
    element.onclick = function () {
      element.disabled = true;
      fetch("/api/asset-specs/" + encodeURIComponent(element.dataset.assetSpecId) + "/generate", {
        method: "POST",
      })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || "Generation could not start.");
            }
            return data;
          });
        })
        .then(function (data) {
          var message = data.execution.outcome === "succeeded"
            ? "Generated Asset v" + data.asset.version + " is registered."
            : data.execution.error_message || "Generation failed and was recorded.";
          say(message);
          return fetch("/api/demo/content");
        })
        .then(function (response) {
          return response.json();
        })
        .then(function (payload) {
          pack(payload.content);
        })
        .catch(function (error) {
          say(error.message || "Generation could not be completed.");
          element.disabled = false;
        });
    };
  });
}

function bindBootstrapReferenceActions() {
  document.querySelectorAll(".bootstrap-reference-asset").forEach(function (element) {
    element.onclick = function () {
      element.disabled = true;
      fetch(
        "/api/asset-specs/" +
          encodeURIComponent(element.dataset.assetSpecId) +
          "/bootstrap-character-reference",
        { method: "POST" }
      )
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || "Bootstrap generation could not start.");
            }
            return data;
          });
        })
        .then(function (data) {
          var message = data.execution.outcome === "succeeded"
            ? "Bootstrap reference candidate Asset v" + data.asset.version + " is registered."
            : data.execution.error_message || "Bootstrap generation failed and was recorded.";
          say(message);
          return fetch("/api/demo/content");
        })
        .then(function (response) { return response.json(); })
        .then(function (payload) { pack(payload.content); })
        .catch(function (error) {
          say(error.message || "Bootstrap generation could not be completed.");
          element.disabled = false;
        });
    };
  });
}

function bindReferenceActions() {
  referenceSelection = [];
  document.querySelectorAll(".reference-candidate").forEach(function (element) {
    element.onchange = function () {
      var assetId = element.dataset.assetId;
      if (element.checked) {
        referenceSelection.push(assetId);
      } else {
        referenceSelection = referenceSelection.filter(function (item) { return item !== assetId; });
      }
    };
  });
  document.querySelectorAll(".create-reference-set").forEach(function (element) {
    element.onclick = function () {
      if (!referenceSelection.length) {
        say("Select one or more eligible hamster Assets first.");
        return;
      }
      element.disabled = true;
      fetch(
        "/api/character-profiles/" +
          encodeURIComponent(element.dataset.characterProfileId) +
          "/reference-sets",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ asset_ids: referenceSelection }),
        }
      )
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || "Reference set could not be created.");
            }
            return data;
          });
        })
        .then(function (data) {
          say("Immutable canonical visual reference set v" + data.reference_set.version + " created.");
          return fetch("/api/demo/content");
        })
        .then(function (response) { return response.json(); })
        .then(function (payload) { pack(payload.content); })
        .catch(function (error) {
          say(error.message || "Reference set could not be created.");
          element.disabled = false;
        });
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
    characterReferenceReview(content.character_reference_review) +
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
  bindGenerationActions();
  bindBootstrapReferenceActions();
  bindReferenceActions();
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
    bindIdeaGateActions();
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
