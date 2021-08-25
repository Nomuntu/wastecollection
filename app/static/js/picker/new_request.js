let coords = null

const locationInput = $('#location')
const manualLocationInput = $('#manual-location')
const gpsAndManualLocFeedback = $('#either-location-invalid-feedback')
const locationFeedback = $('#location-invalid-feedback')

const collectionSubmitButton = $('#collection-submit')
const getLocationButton = $('#location-btn')
const additionalInfoInput = $('#additional-info')

const getLocationButtonDefaultText = $('#location-btn').text()

const data = new FormData()

$(':input').keydown(callOnEnter(submitCollectionForm))

$('textarea').unbind()

manualLocationInput.keydown(clearLocationValidity)

getLocationButton.click(getLocation)
collectionSubmitButton.click(submitCollectionForm)

function clearLocationValidity() {
    clearValidityIndicators(locationInput)
    clearValidityIndicators(manualLocationInput)
    gpsAndManualLocFeedback.hide()
}

function submitCollectionForm() {
    let formValid = true

    const emptyRequestFeedback = $('#empty-request-invalid-feedback')

    emptyRequestFeedback.hide()
    clearLocationValidity()

    if (Object.keys(waste).length < 1) {
        emptyRequestFeedback.show()
        formValid = false
    }

    if (locationInput.attr('placeholder') === undefined && !manualLocationInput.val()) {
        gpsAndManualLocFeedback.text('You need to either get the device location or describe your location manully')
        gpsAndManualLocFeedback.show()

        locationInput.addClass('is-invalid')
        manualLocationInput.addClass('is-invalid')

        formValid = false
    }

    if (formValid) {
        submitForm()
    }
}

function submitForm() {
    collectionSubmitButton.prop('disabled', true)
    collectionSubmitButton.val('Submitting...')

    const request_info = {
        loc: {
            lat: coords?.latitude,
            lon: coords?.longitude,
        },
        manual_loc: manualLocationInput.val(),
        waste: Object.values(waste),
        additional_info: additionalInfoInput.val()
    }

    data.append("info", JSON.stringify(request_info))

    const submit = data => fetch("/api/submit_request", {
        method: "POST",
        body: data
    }).then(res => {
        console.log("Response received:", res)
        if (res.ok) {
            res.text().then(body => location.href = body)
        }
    })

    const image = $('#photo').prop('files')[0]
    new Compressor(image, {
        width: PHOTO_WIDTH,
        success(result) {
            data.append("photo", result)
            submit(data)
        },
        error(err) {
            console.error(`cannot compress image: ${err}, uploading raw`)
            data.append("photo", image)
            submit(data)
        }
    })
}

function getLocation() {
    clearLocationValidity()

    getLocationButton.prop('disabled', true)
    getLocationButton.text('Loading location...')

    navigator.geolocation.getCurrentPosition(
        pos => {
            coords = pos.coords
            const prettyPrint = `${coords.latitude} ${coords.longitude}`
            locationInput.attr('placeholder', prettyPrint)

            restoreGetLocationButton()
        },
        err => {
            locationInput.addClass('is-invalid')
            locationFeedback.text(err.message)
            locationFeedback.show()

            restoreGetLocationButton()
        }
    )
}

function restoreGetLocationButton() {
    getLocationButton.prop('disabled', false)
    getLocationButton.text(getLocationButtonDefaultText)
}
