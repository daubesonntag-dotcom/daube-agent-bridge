import {test} from "node:test";
import assert from "node:assert/strict";
import * as coordinator from "./coordinator.js";

test("Google identity project and zone must both match allowed GCP VM",()=>{
 assert.equal(typeof coordinator.gcpInstanceLocationAllowed,"function");
 assert.equal(coordinator.gcpInstanceLocationAllowed({project_id:"disco-rope-507506-f7",zone:"us-central1-a"}),true);
 assert.equal(coordinator.gcpInstanceLocationAllowed({project_id:"outside-project",zone:"us-central1-a"}),false);
 assert.equal(coordinator.gcpInstanceLocationAllowed({project_id:"disco-rope-507506-f7",zone:"us-central1-b"}),false);
 assert.equal(coordinator.gcpInstanceLocationAllowed({project_id:"disco-rope-507506-f7"}),false);
 assert.equal(coordinator.gcpInstanceLocationAllowed({zone:"us-central1-a"}),false);
 assert.equal(coordinator.gcpInstanceLocationAllowed(null),false);
});
