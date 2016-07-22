<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="ExtractElevationsOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <File Name="InputFile" Label="Input file" ShouldExist="true" FileFilters="All files (*.*)" NumberOfRequiredValues="1"></File>
        <!---AMH this needs to be updated to put in the list of services-->
        <Int Name="Service" Label="Service" NumberOfRequiredValues="1">
          <BriefDescription>Elevation Dataset to use for extraction</BriefDescription>
            <DiscreteInfo DefaultIndex="0">
              <Value Enum="ReplaceMe">ReplaceMe</Value>
            </DiscreteInfo>
        </Int>
        <Int Name="Method" Label="Method" NumberOfRequiredValues="1">
          <BriefDescription>Type of interpolation to use in extraction from raster</BriefDescription>
            <DiscreteInfo DefaultIndex="0">
              <Value Enum="Nearest">0</Value>
              <Value Enum="Bilinear">1</Value>
            </DiscreteInfo>
        </Int>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="ExtractElevationsOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
