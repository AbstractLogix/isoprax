{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Decode where

import Data.Aeson (Object, Value (..))
import qualified Data.Aeson.Key as Key
import qualified Data.Aeson.KeyMap as KeyMap
import Data.Scientific (Scientific, toRealFloat)
import Data.Text (Text)
import qualified Data.Text as Text
import Isoprax.Kernel.Types

field :: Text -> Object -> Maybe Value
field name = KeyMap.lookup (Key.fromText name)

objectValue :: ErrorCategory -> Text -> Value -> Either KernelError Object
objectValue category label value =
  case value of
    Object object -> Right object
    _ -> Left (KernelError category (label <> " must be an object"))

arrayValue :: ErrorCategory -> Text -> Value -> Either KernelError [Value]
arrayValue category label value =
  case value of
    Array values -> Right (foldr (:) [] values)
    _ -> Left (KernelError category (label <> " must be an array"))

textValue :: ErrorCategory -> Text -> Value -> Either KernelError Text
textValue category label value =
  case value of
    String text -> Right text
    _ -> Left (KernelError category (label <> " must be a string"))

boolValue :: ErrorCategory -> Text -> Value -> Either KernelError Bool
boolValue category label value =
  case value of
    Bool result -> Right result
    _ -> Left (KernelError category (label <> " must be a boolean"))

scientificValue :: ErrorCategory -> Text -> Value -> Either KernelError Scientific
scientificValue category label value =
  case value of
    Number number -> Right number
    _ -> Left (KernelError category (label <> " must be a number"))

doubleValue :: ErrorCategory -> Text -> Value -> Either KernelError Double
doubleValue category label value = do
  number <- scientificValue category label value
  let result = toRealFloat number
  if isNaN result || isInfinite result
    then Left (KernelError category (label <> " must be finite"))
    else Right result

requiredField :: ErrorCategory -> Text -> Object -> Either KernelError Value
requiredField category name object =
  maybe
    (Left (KernelError category ("missing field: " <> name)))
    Right
    (field name object)

requiredText :: ErrorCategory -> Text -> Object -> Either KernelError Text
requiredText category name object =
  requiredField category name object >>= textValue category name

optionalText :: ErrorCategory -> Text -> Object -> Either KernelError Text
optionalText category name object =
  case field name object of
    Nothing -> Right ""
    Just Null -> Right ""
    Just value -> textValue category name value

optionalNumber :: ErrorCategory -> Text -> Object -> Either KernelError (Maybe Double)
optionalNumber category name object =
  case field name object of
    Nothing -> Right Nothing
    Just Null -> Right Nothing
    Just value -> Just <$> doubleValue category name value

rejectUnknownFields :: ErrorCategory -> [Text] -> Object -> Either KernelError ()
rejectUnknownFields category allowed object =
  case filter (\candidate -> not (elem candidate allowed)) (map (Key.toText . fst) (KeyMap.toList object)) of
    [] -> Right ()
    firstUnknown : _ ->
      Left (KernelError category ("unknown field: " <> firstUnknown))

nonEmptyText :: ErrorCategory -> Text -> Text -> Either KernelError Text
nonEmptyText category label value
  | Text.null (Text.strip value) = Left (KernelError category (label <> " must be non-empty"))
  | otherwise = Right value

finiteUnitScore :: Text -> Double -> Either KernelError Double
finiteUnitScore label value
  | value < 0 || value > 1 = Left (KernelError InvalidCalibrationInput (label <> " must be in [0, 1]"))
  | otherwise = Right value
