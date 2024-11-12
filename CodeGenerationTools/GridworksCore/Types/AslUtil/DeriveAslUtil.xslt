<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="xml" indent="yes" />
    <xsl:param name="root" />
    <xsl:param name="codee-root" />
    <xsl:include href="../CommonXsltTemplates.xslt"/>
    <xsl:param name="exclude-collections" select="'false'" />
    <xsl:param name="relationship-suffix" select="''" />
    <xsl:variable name="airtable" select="/" />
    <xsl:variable name="squot">'</xsl:variable>
    <xsl:variable name="init-space">             </xsl:variable>
    <xsl:include href="GnfCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>

            <FileSetFile>
                    <xsl:element name="RelativePath"><xsl:text>../../../../src/gjk/named_types/asl_types.py</xsl:text></xsl:element>

                <OverwriteMode>Always</OverwriteMode>
                <xsl:element name="FileContents">
<xsl:text>""" List of all the types used by the actor."""

from typing import Dict, List, no_type_check

from gjk.old_types import GridworksEventSnapshotSpaceheat
from gjk.old_types.batched_readings import BatchedReadings
from gjk.old_types.channel_readings_000 import ChannelReadings000
from gjk.old_types.channel_readings_001 import ChannelReadings001
from gjk.old_types.gridworks_event_gt_sh_status import GridworksEventGtShStatus
from gjk.old_types.gridworks_event_report import GridworksEventReport
from gjk.old_types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.old_types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.old_types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.old_types.gt_sh_status import GtShStatus
from gjk.old_types.report_000 import Report000
from gjk.old_types.report_001 import Report001
from gjk.old_types.report_event_001 import ReportEvent000
from gjk.old_types.snapshot_spaceheat_000 import SnapshotSpaceheat000
from gjk.old_types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat
from gw.named_types import GwBase
</xsl:text>
<xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='gjk')]">
<xsl:sort select="VersionedTypeName" data-type="text"/>
<xsl:variable name="versioned-type-id" select="VersionedType"/>
<xsl:for-each select="$airtable//VersionedTypes/VersionedType[(VersionedTypeId = $versioned-type-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')]">

<xsl:text>
from gjk.named_types.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="TypeName" />
</xsl:call-template>
</xsl:for-each>
</xsl:for-each>
<xsl:text>

TypeByName: Dict[str, GwBase] = {}


@no_type_check
def types() -> List[GwBase]:
    return [
        BatchedReadings,
        ChannelReadings000,
        ChannelReadings001,
        GridworksEventGtShStatus,
        GridworksEventReport,
        GridworksEventSnapshotSpaceheat,
        GtShBooleanactuatorCmdStatus,
        GtShMultipurposeTelemetryStatus,
        GtShSimpleTelemetryStatus,
        GtShStatus,
        Report000,
        Report001,
        ReportEvent000,
        SnapshotSpaceheat000,
        TelemetrySnapshotSpaceheat,
        </xsl:text>
<xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='gjk') and (normalize-space(VersionedTypeName)!='') and (TypeStatus = 'Active' or TypeStatus = 'Pending')]">
<xsl:sort select="VersionedTypeName" data-type="text"/>
<xsl:variable name="versioned-type-id" select="VersionedType"/>
<xsl:for-each select="$airtable//VersionedTypes/VersionedType[(VersionedTypeId = $versioned-type-id)  and (Status = 'Active' or Status = 'Pending')  and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')]">
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="TypeName" />
</xsl:call-template>
</xsl:for-each>


<xsl:choose>
 <xsl:when test="position() != count($airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='gjk')])">
<xsl:text>,
        </xsl:text>
</xsl:when>
<xsl:otherwise>
<xsl:text>,
    </xsl:text>
</xsl:otherwise>
</xsl:choose>
</xsl:for-each>
    <xsl:text>]


for t in types():
    version = t.model_fields["version"].default
    versioned_type_name = f"{t.type_name_value()}.{version}"

    try:
        TypeByName[versioned_type_name] = t
    except Exception:
        print(f"Problem w {t}")
</xsl:text>



                </xsl:element>
            </FileSetFile>


        </FileSet>
    </xsl:template>


</xsl:stylesheet>
