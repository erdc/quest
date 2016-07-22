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
        <Int Name="FileType" Label="File Type" NumberOfRequiredValues="1">
            <DiscreteInfo DefaultIndex="0">
              <Value Enum="USGSDEM">0</Value>
              <Value Enum="GTIFF">0</Value>
              <Value Enum="PNG">0</Value>
              <Value Enum="JPG">0</Value>
            </DiscreteInfo>
        </Int>
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
