function applyCampAnimationLogic(camp) {
    // Camp is affected by bikes - apply animation logic for powering up/on/down/off
    if (camp["triggered_by_bikes"] === true) {
        if (campBikeCounts !== undefined) {
            if (campBikeCounts[camp["name"]] > 0) {
                if (camp["current_state"] == "POWERED_DOWN") {
                    beginPowerUpAni(camp)
                } else if (camp["current_state"] == "POWERING_UP") {
                    tickPowerUpAni(camp)
                } else if (camp["current_state"] == "POWERED_ON") {
                    loopPoweredOnAni(camp)
                } else if (camp["current_state"] == "POWERING_DOWN") {
                    // Keep the animations graceful by reversing the powering down ani
                    // if bikes rejoin the camp while we're still powering down
                    reversePowerDownAni(camp)
                }
            } else {
                if (camp["current_state"] == "POWERING_UP") {
                    // Keep the animations graceful by reversing the powering up ani
                    // if bikes leave the camp while we're still powering up
                    reversePowerUpAni(camp)
                } else if (camp["current_state"] == "POWERED_ON") {
                    beginPowerDownAniASAP(camp)
                } else if (camp["current_state"] == "POWERING_DOWN") {
                    tickPowerDownAni(camp)
                } else if (camp["current_state"] == "POWERED_DOWN") {
                    setPoweredOffFrame(camp)
                }
            }
        }
    } else {
        // Camp is not affected by bikes - just loop its powered on animation
        loopPoweredOnAni(camp)
    }

    return camp
}

function applySimpleCampAnimationLogic(camp) {
    return camp
}

function setPoweredOffFrame(camp) {
    camp["current_state"] = "POWERED_DOWN"
    camp["current_frame"] = camp["states"]["powered_off"]["frame_start"]
}

function beginPowerUpAni(camp) {
    camp["current_state"] = "POWERING_UP"
    camp["current_frame"] = camp["states"]["powering_up"]["frame_start"]
}

function tickPowerUpAni(camp) {
    camp["current_state"] = "POWERING_UP"
    camp["current_frame"] += 1

    if (camp["current_frame"] > camp["states"]["powering_up"]["frame_end"]) {
        camp["current_state"] = "POWERED_ON"
    }
}

function reversePowerUpAni(camp) {
    camp["current_state"] = "POWERING_UP"
    camp["current_frame"] -= 1

    if (camp["current_frame"] <= camp["states"]["powering_up"]["frame_start"]) {
        camp["current_state"] = "POWERED_DOWN"
    }
}

function loopPoweredOnAni(camp) {
    camp["current_state"] = "POWERED_ON"
    camp["current_frame"] += 1

    if (camp["current_frame"] > camp["states"]["powered_on"]["frame_end"]) {
        camp["current_frame"] = camp["states"]["powered_on"]["frame_start"]
    }
}

function beginPowerDownAni(camp) {
    camp["current_state"] = "POWERING_DOWN"
    camp["current_frame"] = camp["states"]["powering_down"]["frame_start"]
}

function beginPowerDownAniASAP(camp) {
    halfwayPoint =
        camp["states"]["powered_on"]["frame_start"] +
        (camp["states"]["powered_on"]["frame_end"] - camp["states"]["powered_on"]["frame_start"]) / 2

    if (camp["current_frame"] <= halfwayPoint) {
        camp["current_frame"] -= 1

        if (camp["current_frame"] < camp["states"]["powered_on"]["frame_start"]) {
            beginPowerDownAni(camp)
        }
    } else {
        camp["current_frame"] += 1

        if (camp["current_frame"] > camp["states"]["powered_on"]["frame_end"]) {
            beginPowerDownAni(camp)
        }
    }
}

function tickPowerDownAni(camp) {
    camp["current_state"] = "POWERING_DOWN"
    camp["current_frame"] += 1

    if (camp["current_frame"] >= camp["states"]["powering_down"]["frame_end"]) {
        camp["current_state"] = "POWERED_DOWN"
    }
}

function reversePowerDownAni(camp) {
    camp["current_state"] = "POWERING_DOWN"
    camp["current_frame"] -= 1

    if (camp["current_frame"] <= camp["states"]["powering_down"]["frame_start"]) {
        camp["current_state"] = "POWERED_ON"
        camp["current_frame"] = camp["states"]["powered_on"]["frame_start"]
    }
}
