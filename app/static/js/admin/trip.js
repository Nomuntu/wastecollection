const driverSelector = $('#driver-selector')
const dateSelector = $('#date-selector')
const deleteTripButton = $('#delete-trip')
const submitChangesButton = $('#submit-changes')
const tableRowSelector = $('.clickable-table-row')

let removed_requests = []

submitChangesButton.on('click', submitTripChanges)

$(document).ready(_ => {
    setMinDateSelector()

    driverSelector.change(_ => clearValidityIndicators(driverSelector))
    dateSelector.change(_ => clearValidityIndicators(dateSelector))

    const collection_date = $('#edit-details').attr('data-value')

    if (collection_date === 'None') {
        $('#edit-details').attr('hidden', false)
    }

    $('#submit-trip').on('click', e => {
        const driverSelected = validateDriverSelected()
        const dateSelected = validateDateSelected()
        if (driverSelected && dateSelected) {
            const driver = driverSelector.find('option:selected')

            const data = {
                driverId: driver.val(),
                timestamp: new Date(dateSelector.val()).valueOf()
            }

            const url = e.currentTarget.getAttribute('data-value')

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }).then(res => {
                alert('Trip scheduled')
                console.log(res)
                location.reload()
            })
        }
    })
})

tableRowSelector.on('click', 'td .remove-request', e => {
    e.stopPropagation()
    const id = e.currentTarget.getAttribute("data-value")
    removed_requests.push(id)
    $(`#row_${id}`).remove()
    e.stopPropagation()
})

tableRowSelector.on('click', e => {
    const id = e.currentTarget.getAttribute("data-value")
    location.href = `/admin/view_request/${id}`
})

function setMinDateSelector() {
    const DAYS_MILLIS = 24 * 60 * 60 * 1000
    const todayDate = new Date(Date.now() + DAYS_MILLIS)
    const todayStr = yearMonthDay(todayDate)
    $('#date-selector').attr('min', todayStr)
}

function validateDriverSelected() {
    clearValidityIndicators(driverSelector)

    const invalidDriver = driverSelector.find('option:selected').prop('disabled')

    if (invalidDriver) {
        driverSelector.addClass('is-invalid')
    } else {
        driverSelector.addClass('is-valid')
    }

    return !invalidDriver
}

function validateDateSelected() {
    clearValidityIndicators(dateSelector)

    const dateIsSelected = dateSelector.val().length !== 0
    const dateIsValid = dateIsSelected ? (new Date(dateSelector.val()) > Date.now()) : false

    if (dateIsValid) {
        dateSelector.addClass('is-valid')
    } else {
        dateSelector.addClass('is-invalid')
    }

    return dateIsValid
}

function yearMonthDay(date) {
    return date.toISOString().substring(0, 10)
}

function submitTripChanges() {
    const driverSelected = validateDriverSelected()
    const dateSelected = validateDateSelected()

    if (driverSelected && dateSelected) {
        submitChangesButton.prop('disabled', true)
        submitChangesButton.val('Updating...')

        const driver = driverSelector.find('option:selected')
        const trip_id = submitChangesButton.attr('data-value')
        const trip_info = {
            id: trip_id,
            driverId: driver.val(),
            timestamp: new Date(dateSelector.val()).valueOf(),
            removed_requests: removed_requests
        }

        const data = JSON.stringify(trip_info)

        fetch("/api/admin/update_trip", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: data
        }).then(res => {
            alert('Trip updated')
            console.log(res)
            location.reload()
        })
    }
}

function addRemovalButtons() {
    $('#requests > thead > tr').append("<th scope=\"col\">Remove Request From Trip</th>")
    $('#requests > tbody > tr').each(function() {
        const req_id = $(this).attr('data-value')
        $(this).append(`<td><button type=\"button\" data-value=\"${req_id}\" class=\"remove-request btn btn-danger entry-delete-btn\">Remove</button></td>`)
    })
}

$('#edit-trip').on('click', _ => {
    $('#edit-details').removeAttr('hidden')
    submitChangesButton.removeAttr('hidden')
    $('#edit-trip').attr('hidden', true)
    $('#submit-trip').attr('hidden', true)
    addRemovalButtons()
})

deleteTripButton.on('click', _ => {
    const trip_id = deleteTripButton.attr('data-value')
    const data = JSON.stringify({
        id: trip_id
    })

    const confirmed = window.confirm('Are you sure you want to delete this trip? This cannot be undone.')

    if (!confirmed) {
        return
    }

    const responseFuture = fetch("/api/admin/delete_trip", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    })

    deleteTripButton.prop('disabled', true)

    responseFuture.then(res => {
        console.log("Response received:", res)
        location.href = '/admin'
    })
})
