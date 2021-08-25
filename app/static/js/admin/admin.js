const newTripSubmitButton = $('#new-trip-submit-button')

function enableTripCreation() {
    newTripSubmitButton.removeAttr('disabled')
}

function disableTripCreation() {
    newTripSubmitButton.attr('disabled', true)
}

function moveToScheduled(reqIds) {
    // Untick all checkboxes
    $('#pending-requests tbody tr td input').prop('checked', false)

    const pendingTable = $('#pending-requests').dataTable()
    const scheduledTable = $('#scheduled-requests').dataTable()

    reqIds.forEach(reqId => {
        const tableRow = $(`#${reqId}`)
        const tableRowCells = tableRow.find('td')
        const rowIndex = scheduledTable.fnAddData([
            tableRowCells.eq(1).html(),
            tableRowCells.eq(2).html(),
            tableRowCells.eq(3).html(),
            tableRowCells.eq(4).html()
        ])

        const newRow = $(scheduledTable.fnGetNodes(rowIndex))

        newRow.attr('id', `${reqId}`)
        newRow.attr('data-value', `/admin/view_request/${reqId}`)
        newRow.addClass('clickable-table-row')

        pendingTable.fnDeleteRow(tableRow)
    })
}

newTripSubmitButton.on('click', _ => {
    const reqIds = getSelectedMarkerIds()
    const tripId = $('#trip-selector option:selected').val()

    const responseFuture = fetch('/api/admin/add_to_trip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tripId: tripId,
            reqIds: reqIds
        })
    })

    disableTripCreation()
    moveToScheduled(reqIds)
    setRowEvents()
    // Deselect markers, and remove them from map
    reqIds.forEach(reqId => deSelectMarker(markerMap[reqId]))
    reqIds.forEach(reqId => removeMarkerFromMap(markerMap[reqId]))

    responseFuture.then(res => {
        console.log('Response received', res)
        location.reload()
    })
})

function setRowEvents(){
    // Stops the checkbox being clicked on
    $('.clickable-table-row').on('click', 'td .form-check-input', e => {
        e.stopPropagation()
        const thisBox = e.currentTarget
        const reqId = thisBox.getAttribute('data-value')

        if (thisBox.checked) {
            selectMarker(markerMap[reqId])
            enableTripCreation()
        } else {
            deSelectMarker(markerMap[reqId])

            if (getSelectedMarkerIds().length === 0) {
                disableTripCreation()
            }
        }
    })

    $('.clickable-table-row').on('click', '.checkbox-col', e => e.stopPropagation())
    $('.clickable-table-row').on('click', e => location = e.currentTarget.getAttribute("data-value"))

    // Green pin on hover
    $('#pending-requests tbody .clickable-table-row').hover(ev => {
        const id = ev.target.parentNode.id
        $(`#req-${id}`).css({'color': '#198754'})
    }, ev => {
        const id = ev.target.parentNode.id
        $(`#req-${id}`).css({'color': ''})
    })

    // Tooltip on row without location
    $('.tooltip-wrapper').each((_, wrapper) => {
        if (wrapper.firstElementChild.disabled){
            wrapper.setAttribute("title", "They have not provided their location. Please edit the request to specify their location before assigning to a trip")
            new bootstrap.Tooltip(wrapper, {})
        }
    })
}

const DATA_TABLE_OPTIONS = numCols => {
    return {
        scrollX: true,
        order: [[numCols - 2, 'desc']]
    }
}

const withKey = (object, key, value) => {
    object[key] = value
    return object
}

const TRANSITION_INSTANT = {
    '-webkit-transition-delay': '0s',
    'transition-delay': '0s',
    'transition': 'height 0s'
}
const TRANSITION_DEFAULT = {
    '-webkit-transition-delay': '',
    'transition-delay': '',
    'transition': ''
}

$(document).ready(function () {
    $('#pending-requests').DataTable(
        withKey(
            DATA_TABLE_OPTIONS(4),
            'columnDefs',
            [{orderable: false, targets: 0}]
        )
    )
    $('#scheduled-requests').DataTable(DATA_TABLE_OPTIONS(3))
    $('#completed-requests').DataTable(DATA_TABLE_OPTIONS(3))

    const scheduledPanel = $('#scheduled-panel')
    const completedPanel = $('#completed-panel')

    // temporarily set transition time to 0s to make movement on load quicker
    scheduledPanel.css(TRANSITION_INSTANT)
    completedPanel.css(TRANSITION_INSTANT)

    scheduledPanel.collapse()
    completedPanel.collapse()

    scheduledPanel.css(TRANSITION_DEFAULT)
    completedPanel.css(TRANSITION_DEFAULT)

    setRowEvents()
})

// realign datatables after accordion opening
$('.accordion').on('shown.bs.collapse', _ => {
    $($.fn.dataTable.tables(true)).DataTable().columns.adjust()
});

const socket = io()
socket.on("connect", () => {
    console.log(socket.id);
})
socket.on("data", (r) => {
    const req = JSON.parse(r.req)
    const tr = `
        <tr class="clickable-table-row" id="${req.id}" data-value="/admin/view_request/${req.id}">
          <td class="checkbox-col">
            <div class="tooltip-wrapper" data-bs-toggle="tooltip">
                <input data-value="${req.id}"
                       class="form-check-input"
                       type="checkbox"
                       ${req.address === null ? "disabled": ""}>
           </div>
          </td>
          <td>${req.name}</td>
          <td><span style="display: none;">${req.timestamp}</span>${req.date}</td>
          <td>${req.address === null ? "None" : req.address}</td>
        </tr>
`
    $('#pending-requests').DataTable().row.add($(tr)).draw()
    console.log(req)
    const pin = JSON.parse(r.pin)
    if (pin !== null){
        registerPin({ loc: [pin.lat, pin.lon], reqId: pin.reqId, msg: pin.msg })
    }
    setRowEvents()
})


