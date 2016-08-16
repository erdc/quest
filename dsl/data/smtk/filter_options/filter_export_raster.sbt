<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="ExportRasterOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <String Name="filename" Label="Filename" >
          <BriefDescription>Without the extension</BriefDescription>
        </String>
        <String Name="FileType" Label="File Type" NumberOfRequiredValues="1">
            <DiscreteInfo DefaultIndex="0">
              <Value Enum="USGSDEM">USGSDEM</Value>
              <Value Enum="GTIFF">GTIFF</Value>
              <Value Enum="PNG">PNG</Value>
              <Value Enum="JPG">JPG</Value>
            </DiscreteInfo>
        </String>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="ExportRasterOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
