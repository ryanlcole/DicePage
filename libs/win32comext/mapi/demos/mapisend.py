#!/usr/bin/env python

"""module to send mail with Extended MAPI using the pywin32 mapi wrappers..."""

# 051434.python.mapisend.line5.comment this was based on Jason Hattingh's C++ code at http://www.codeproject.com/internet/mapadmin.asp (dead link)
# 051435.python.mapisend.line6.comment written by David Fraser <davidf at sjsoft.com> and Stephen Emslie <stephene at sjsoft.com>
# 051436.python.mapisend.line7.comment you can test this by changing the variables at the bottom and running from the command line

from win32com.mapi import mapi, mapitags


def SendEMAPIMail(
    Subject="", Message="", SendTo=None, SendCC=None, SendBCC=None, MAPIProfile=None
):
    """Sends an email to the recipient using the extended MAPI interface
    Subject and Message are strings
    Send{To,CC,BCC} are comma-separated address lists
    MAPIProfile is the name of the MAPI profile"""

    # 051437.python.mapisend.line20.comment initialize and log on
    mapi.MAPIInitialize(None)
    session = mapi.MAPILogonEx(
        0, MAPIProfile, None, mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT
    )
    messagestorestable = session.GetMsgStoresTable(0)
    messagestorestable.SetColumns(
        (mapitags.PR_ENTRYID, mapitags.PR_DISPLAY_NAME_A, mapitags.PR_DEFAULT_STORE), 0
    )

    while True:
        rows = messagestorestable.QueryRows(1, 0)
        # 051438.python.mapisend.line32.comment if this is the last row then stop
        if len(rows) != 1:
            break
        row = rows[0]
        # 051439.python.mapisend.line36.comment if this is the default store then stop
        if (mapitags.PR_DEFAULT_STORE, True) in row:
            break

    # 051440.python.mapisend.line40.comment unpack the row and open the message store
    (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
    msgstore = session.OpenMsgStore(
        0, eid, None, mapi.MDB_NO_DIALOG | mapi.MAPI_BEST_ACCESS
    )

    # 051441.python.mapisend.line46.comment get the outbox
    hr, props = msgstore.GetProps((mapitags.PR_IPM_OUTBOX_ENTRYID), 0)
    (tag, eid) = props[0]
    # 051442.python.mapisend.line49.comment check for errors
    if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
        raise TypeError("got PT_ERROR instead of PT_BINARY: %s" % eid)
    outboxfolder = msgstore.OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

    # 051443.python.mapisend.line54.comment create the message and the addrlist
    message = outboxfolder.CreateMessage(None, 0)
    # 051444.python.mapisend.line56.comment note: you can use the resolveaddress functions for this. but you may get headaches
    pal = []

    def makeentry(recipient, recipienttype):
        return (
            (mapitags.PR_RECIPIENT_TYPE, recipienttype),
            (mapitags.PR_SEND_RICH_INFO, False),
            (mapitags.PR_DISPLAY_TYPE, 0),
            (mapitags.PR_OBJECT_TYPE, 6),
            (mapitags.PR_EMAIL_ADDRESS_A, recipient),
            (mapitags.PR_ADDRTYPE_A, "SMTP"),
            (mapitags.PR_DISPLAY_NAME_A, recipient),
        )

    if SendTo:
        pal.extend(
            [makeentry(recipient, mapi.MAPI_TO) for recipient in SendTo.split(",")]
        )
    if SendCC:
        pal.extend(
            [makeentry(recipient, mapi.MAPI_CC) for recipient in SendCC.split(",")]
        )
    if SendBCC:
        pal.extend(
            [makeentry(recipient, mapi.MAPI_BCC) for recipient in SendBCC.split(",")]
        )

    # 051445.python.mapisend.line83.comment add the resolved recipients to the message
    message.ModifyRecipients(mapi.MODRECIP_ADD, pal)
    message.SetProps([(mapitags.PR_BODY_A, Message), (mapitags.PR_SUBJECT_A, Subject)])

    # 051446.python.mapisend.line87.comment save changes and submit
    outboxfolder.SaveChanges(0)
    message.SubmitMessage(0)


if __name__ == "__main__":
    MAPIProfile = ""
    # 051447.python.mapisend.line94.comment Change this to a valid email address to test
    SendTo = "an.invalid at address"
    SendMessage = "testing one two three"
    SendSubject = "Testing Extended MAPI!!"
    SendEMAPIMail(SendSubject, SendMessage, SendTo, MAPIProfile=MAPIProfile)
