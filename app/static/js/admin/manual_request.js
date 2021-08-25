let coords = {}

const locationInput = $('#location')
const collectionSubmitButton = $('#collection-submit')

const data = new FormData()

$(':input').keydown(callOnEnter(submitCollectionForm))

collectionSubmitButton.click(submitCollectionForm)

map.on('click', ev => {
    const latlng = getClickedLocation(ev, locationInput, manualInputMarker)
    coords.latitude = latlng.lat
    coords.longitude = latlng.lng
})

const manualInputMarker = makeMarker(undefined, UNSELECTED_REQ_ICON)

function submitCollectionForm() {
    let formValid = true

    const emptyRequestFeedback = $('#empty-request-invalid-feedback')

    emptyRequestFeedback.hide()
    clearValidityIndicators(locationInput)

    const name = $('#name').val()
    const phoneNumber = $('#phone-number').val().replace(/\s+/g, '')

    if (!validateName(name, $('#name'))) {
        formValid = false
    }

    if (!validatePhoneNumber(phoneNumber, $('#phone-number'))) {
        formValid = false
    }

    if (Object.keys(waste).length < 1) {
        emptyRequestFeedback.show()
        formValid = false
    }

    if (locationInput.attr('placeholder') === undefined) {
        $('#location-invalid-feedback').text('Did you forget to pick a location?')
        locationInput.addClass('is-invalid')
        formValid = false
    }

    if (formValid) {
        submitForm(name, phoneNumber)
    }
}

function submitForm(name, phoneNumber) {
    const request_info = {
        name: name,
        phone: phoneNumber,
        loc: {
            lat: coords.latitude,
            lon: coords.longitude,
        },
        waste: Object.values(waste),
    }
    data.append("info", JSON.stringify(request_info))

    const image = $('#photo').prop('files')[0]
    data.append("photo", image)

    const response_future = fetch("/api/admin/submit_manual_request", {
        method: "POST",
        body: data
    })

    collectionSubmitButton.prop('disabled', true)
    collectionSubmitButton.val('Submitting...')

    response_future.then(res => {
        console.log("Response received:", res)
        location.href = '/admin'
    })
}

