const locationInput = $('#location')
const manualInputMarker = makeMarker(undefined, UNSELECTED_REQ_ICON)
const submitChangesButton = $('#submit-changes')
const nameInput = $('#name')
const phoneInput = $('#phone-number')

let latlng

submitChangesButton.on('click', validateRequest)

function makeMapEditable() {
    const map_div = $('#map')
    map_div.addClass('mb-4')
    map_div.attr('height', '500px')

    $('#edit-map-prompt').removeAttr('hidden')
    $('#edit-map-submit').removeAttr('hidden')

    map.on('click', ev => {
        latlng = getClickedLocation(ev, locationInput, manualInputMarker)
    })
}

function makeDetailsEditable() {
    nameInput.attr('readonly', false)
    nameInput.css('border', 'solid')
    nameInput.addClass('is-valid')

    phoneInput.attr('readonly', false)
    phoneInput.css('border', 'solid')
    phoneInput.addClass('is-valid')
    $('#call-link').hide()

    $('#location-edit-prompt').removeAttr('hidden')
    $('#mark-as-complete-button').parent().attr('hidden', true)
}

function validateRequest() {
    let formValid = true

    const emptyRequestFeedback = $('#empty-request-invalid-feedback')

    emptyRequestFeedback.hide()
    clearValidityIndicators(locationInput)

    const name = nameInput.val()
    const phoneNumber = phoneInput.val().replace(/\s+/g, '')

    if (!validateName(name, nameInput)) {
        formValid = false
    }

    if (!validatePhoneNumber(phoneNumber, phoneInput)) {
        formValid = false
    }

    if (Object.keys(waste).length < 1) {
        emptyRequestFeedback.show()
        formValid = false
    }

    if (formValid) {
        submitChanges(name, phoneNumber)
    }
}

function submitChanges(name, phoneNumber) {
    const req_id = submitChangesButton.attr('data-value')
    const request_info = {
        id: req_id,
        name: name,
        phone: phoneNumber,
        waste_entries: Object.values(waste)
    }

    if (latlng) {
        request_info.loc = {
            lat: latlng.lat,
            lon: latlng.lng,
        }
    }

    const data = JSON.stringify(request_info)

    const responseFuture = fetch("/api/admin/update_request", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    })

    submitChangesButton.prop('disabled', true)
    submitChangesButton.val('Updating...')

    responseFuture.then(res => {
        console.log("Response received:", res)
        location.reload()
    })
}

function markAsComplete(id, elem) {
    const failureFeedback = $('#marking-failure-feedback')
    failureFeedback.hide()

    const responseFuture = fetch(`/api/mark_as_complete/${id}`)

    elem.setAttribute('disabled', true)
    elem.innerHTML = "Marking..."

    const handleFailure = function () {
        failureFeedback.text("Marking failed, please try again")
        failureFeedback.show()

        elem.removeAttribute('disabled')
        elem.innerHTML = "Mark as complete"
    }

    responseFuture.then(resp => {
        if (resp.ok) {
            elem.innerHTML = "Collection has been completed"
        } else {
            console.error(resp)
            handleFailure()
        }
    }).catch(error => {
        console.error(error)
        handleFailure()
    })

}

$('#edit-request').on('click', _ => {
    makeMapEditable()
    makeDetailsEditable()
    $('#waste-entry-control').removeAttr('hidden')
    $('.entry-delete-btn').removeAttr('hidden')
    submitChangesButton.removeAttr('hidden')
    $('#edit-request').attr('hidden', true)
    $('#no-loc-warning').attr('hidden', true)
})

$('#delete-request').on('click', _ => {
    const deleteRequestButton = $('#delete-request')
    const req_id = deleteRequestButton.attr('data-value')
    const data = JSON.stringify({id: req_id})

    const confirmed = window.confirm('Are you sure you want to delete this request? This cannot be undone.')

    if (!confirmed) {
        return
    }

    const responseFuture = fetch("/api/admin/delete_request", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    })

    deleteRequestButton.prop('disabled', true)

    responseFuture.then(res => {
        console.log("Response received:", res)
        location.href = '/admin'
    })
})
